#!/usr/bin/env bash
FILE_SIGNATURE=2017.11.21-v1-jef
COUNTRY_ROUND=KER6

DIR=form_changes/from_template/fq/
FILE_NAME_VAR=from_Template_FQ
python -m pmix.viffer ${DIR}1.xlsx ${DIR}2.xlsx > ${DIR}${COUNTRY_ROUND}_Form_Changes_${FILE_NAME_VAR}_${FILE_SIGNATURE}.csv
DIR=form_changes/from_template/hq/
FILE_NAME_VAR=from_Template_HQ
python -m pmix.viffer ${DIR}1.xlsx ${DIR}2.xlsx > ${DIR}${COUNTRY_ROUND}_Form_Changes_${FILE_NAME_VAR}_${FILE_SIGNATURE}.csv
DIR=form_changes/from_template/sq/
FILE_NAME_VAR=from_Template_SQ
python -m pmix.viffer ${DIR}1.xlsx ${DIR}2.xlsx > ${DIR}${COUNTRY_ROUND}_Form_Changes_${FILE_NAME_VAR}_${FILE_SIGNATURE}.csv
DIR=form_changes/from_previous_round/fq/
FILE_NAME_VAR=from_PreviousRound_FQ
python -m pmix.viffer ${DIR}1.xlsx ${DIR}2.xlsx > ${DIR}${COUNTRY_ROUND}_Form_Changes_${FILE_NAME_VAR}_${FILE_SIGNATURE}.csv
DIR=form_changes/from_previous_round/hq/
FILE_NAME_VAR=from_PreviousRound_HQ
python -m pmix.viffer ${DIR}1.xlsx ${DIR}2.xlsx > ${DIR}${COUNTRY_ROUND}_Form_Changes_${FILE_NAME_VAR}_${FILE_SIGNATURE}.csv
DIR=form_changes/from_previous_round/sq/
FILE_NAME_VAR=from_PreviousRound_SQ
python -m pmix.viffer ${DIR}1.xlsx ${DIR}2.xlsx > ${DIR}${COUNTRY_ROUND}_Form_Changes_${FILE_NAME_VAR}_${FILE_SIGNATURE}.csv
