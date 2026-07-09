use tests/fixtures/dataset/auto.dta, clear
sum price mpg
regress price mpg weight foreign
