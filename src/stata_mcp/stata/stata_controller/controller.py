#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam
# @Email  : sepinetam@gmail.com
# @File   : controller.py

import re
import time

import pexpect


class StataController:
    def __init__(self, stata_cli: str = None, timeout: int = 30):
        """
        Initialize the Stata controller.

        Args:
            stata_cli (str): Path to the Stata command-line executable.
            timeout (int): Timeout for command execution (in seconds).
        """
        self.stata_cli_path = stata_cli
        self.child = None
        self.timeout = timeout
        self.start()

    @property
    def STATA_CLI(self):
        return self.stata_cli_path

    def _expect_prompt(self, timeout=None):
        """
        Wait for the Stata prompt, indicating command completion.

        Args:
            timeout (int, optional): Timeout for this wait; if not provided, use default.

        Returns:
            int: The index returned by pexpect.expect.
        """
        if timeout is None:
            timeout = self.timeout

        # Use a set of patterns to match various prompt scenarios
        patterns = [
            r"\r\n\. ",  # Standard prompt
            r"\r\n: ",  # Continuation prompt
            r"\r\n--more--",  # More content prompt
            r"r\(\d+\);",  # Error prompt
            pexpect.TIMEOUT,  # Timeout
            pexpect.EOF,  # End of program
        ]

        index = self.child.expect(patterns, timeout=timeout)

        # Handle matched patterns
        if index == 2:  # --more-- prompt; send space to continue
            self.child.send(" ")
            return self._expect_prompt(timeout)  # Recurse until actual prompt
        elif index == 3:  # Error prompt
            # Continue waiting until standard prompt appears
            try:
                self.child.expect(r"\r\n\. ", timeout=5)
            except pexpect.TIMEOUT:
                pass  # Ignore timeout and return error index
            return index
        elif index == 4:  # Timeout
            # Try sending a newline to trigger the prompt
            self.child.sendline("")
            try:
                return self.child.expect(
                    [r"\r\n\. ", pexpect.TIMEOUT], timeout=5)
            except pexpect.TIMEOUT:
                return index

        return index

    def run(self, command, timeout=None):
        """
        Execute a Stata command and wait for completion.

        Args:
            command (str): The Stata command to execute.
            timeout (int, optional): Timeout for this command.

        Returns:
            str: The output of the command execution.

        Raises:
            RuntimeError: If the command times out or other errors occur.
        """
        if timeout is None:
            timeout = self.timeout

        # Send the command
        self.child.sendline(command)

        # Wait for the command to complete
        result = self._expect_prompt(timeout)

        # Capture the output
        output = self.child.before.strip()

        # Check for errors
        if result == 3:  # Error prompt index
            error_match = re.search(r"r\((\d+)\);", output)
            if error_match:
                error_code = error_match.group(1)
                raise RuntimeError(f"Stata error r({error_code}): {output}")
        elif result == 4:  # Timeout
            raise RuntimeError(f"Command timed out (> {timeout}s): {command}")
        elif result == 5:  # EOF
            raise RuntimeError(
                f"Stata session terminated unexpectedly: {output}")

        return output

    def run_with_retry(self, command, max_retries=3, timeout=None):
        """
        Execute a command with a retry mechanism.

        Args:
            command (str): The Stata command to execute.
            max_retries (int): Maximum number of retry attempts.
            timeout (int, optional): Timeout for this command.

        Returns:
            str: The output of the command execution.

        Raises:
            RuntimeError: If all retry attempts fail.
        """
        retries = 0
        last_error = None

        while retries < max_retries:
            try:
                return self.run(command, timeout)
            except RuntimeError as e:
                last_error = e
                retries += 1
                # If it's a timeout error and we can retry, restart the session
                if "timed out" in str(e) and retries < max_retries:
                    self.restart()
                time.sleep(1)  # Brief pause before retry

        # All retries failed
        raise RuntimeError(
            f"Command failed after {max_retries} attempts: {last_error}")

    def start(self):
        """
        Start the Stata session.
        """
        self.child = pexpect.spawn(
            self.STATA_CLI, encoding="utf-8", timeout=self.timeout
        )
        self._expect_prompt()

    def restart(self):
        """
        Restart the Stata session.
        """
        self.close()
        self.start()

    def close(self):
        """
        Close the Stata session.
        """
        if self.child and not self.child.closed:
            try:
                self.child.sendline("exit, clear")
                self.child.expect(pexpect.EOF, timeout=5)
            except Exception as e:
                print(
                    f"Warning: Could not close Stata session with error: {e}")
            finally:
                self.child.close()


if __name__ == "__main__":
    url = "https://pub-b55c5837ee41480ba0f902096dd9725d.r2.dev/01_OLS.dta"
    stata_cli = "stata-mp"
    var_list = []  # e.g., ["weight", "height"]
    var_str = " ".join(var_list) if var_list else ""

    # Use a longer timeout for the session
    temp_stata_session = StataController(stata_cli=stata_cli, timeout=60)

    try:
        # Execute command with retry
        use_data = temp_stata_session.run_with_retry(f"use {url}, clear")
        if "not found" in use_data or "server reported server error" in use_data:
            print("Stata data not found. Please check the path.")
        else:
            # For commands that may require more time, specify a longer timeout
            summarize = temp_stata_session.run(
                f"summarize {var_str}", timeout=120)
            describe = temp_stata_session.run(f"describe {var_str}")
            result = {"summarize": summarize, "describe": describe}
            print(result.get("summarize"))
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Ensure the session is properly closed
        temp_stata_session.close()
