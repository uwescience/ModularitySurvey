# Survey of Moduarity in Biology

This repository contains a database for a survey of literature on modularity in biology.

You can access the databse using
[this url](https://lite.datasette.io/?csv=https://raw.githubusercontent.com/uwescience/ModularitySurvey/main/db/modularity_survey.csv)

## Usage

* List column names
    SELECT name FROM pragma_table_info('modularity_survey');
* Show all rows
    SELECT * from modularity_survey
* Show rows with just Hellerstein AddedBy
    SELECT * from modularity_survey where AddedBy="Hellerstein"