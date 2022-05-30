import streamlit as st
import pandas as pd
import os

from io import BytesIO
import base64
from pyxlsb import open_workbook as open_xlsb
import zipfile
from datetime import datetime

from ruleParser import *

st.set_page_config(page_title='BriefCatch Wizard', page_icon=':briefcase:')

# ==================================================================
# LOADING THE NGRAMS FROM FILES
# ==================================================================
@st.cache(allow_output_mutation=True, suppress_st_warning=True)
def load_ngrams_zip():
	dfs_all = {}
	load_bar = st.progress(0)
	for i in range(1,6):
		fpath = os.path.join(os.path.join(os.getcwd(),'ngrams'),'ngrams_'+str(i)+'.zip')
		dfs_all[i] = pd.read_csv(fpath,sep='\t',compression='zip')
		progress_value = int(i * (100/5))
		load_bar.progress(progress_value)
	return dfs_all

dropbox_urls = {
	1 : 'https://www.dropbox.com/s/wlhv36a0q2skw1c/ngrams_1.zip?dl=1',
	2 : 'https://www.dropbox.com/s/f0auhdapmao5wsp/ngrams_2.zip?dl=1',
	3 : 'https://www.dropbox.com/s/nufozjz94wxvozk/ngrams_3.zip?dl=1',
	4 : 'https://www.dropbox.com/s/kcybqkdlal7qyaq/ngrams_4.zip?dl=1',
	5 : 'https://www.dropbox.com/s/okmnzvk72sz1lh3/ngrams_5.zip?dl=1'
}

@st.cache(allow_output_mutation=True, suppress_st_warning=True)
def load_ngrams_url():
	dfs_all = {}
	load_bar = st.progress(0)
	for i in range(1,6):
		dfs_all[i] = pd.read_csv(dropbox_urls[i],sep='\t',compression='zip')
		progress_value = int(i * (100/5))
		load_bar.progress(progress_value)
	return dfs_all

dfs = load_ngrams_url()


# ====================================================================
# FUNCTIONALITY
# ====================================================================
def dfDict_to_excel(df0,dfDict):
	output = BytesIO()
	writer = pd.ExcelWriter(output, engine='xlsxwriter')
	df0.to_excel(writer,index=False,sheet_name='Rule')
	for key in dfDict:
		dfDict[key].to_excel(writer, index=False, sheet_name=str(key)+'-gram')	
	writer.save()
	processed_data = output.getvalue()
	#href = f'<a href="data:file/txt;base64,{b64} downlad="{new_filename}">Click Here!</a>'
	return processed_data

def df_to_excel(mydf):
	output = BytesIO()
	writer = pd.ExcelWriter(output, engine='xlsxwriter')
	mydf.to_excel(writer,index=False,sheet_name='Results')
	writer.save()
	processed_data = output.getvalue()
	return processed_data

def generateResultsAll(inputRuleDict):
	outputResults = []
	for r in inputRuleDict:
		ruleID = r
		ruleLst = inputRuleDict[r]
		ruleDF0 = pd.DataFrame({'Rule / Pattern': ruleLst[0], 'Correction / Recommendation': ruleLst[1], 'Rule ID': [ruleID]})
		searchTxt = ruleLst[0]
		# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
		#st.write('Processing ' + searchTxt)
		# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

		resultDFs = {}
		# WRAP IN TRY CATCH STATEMENT, SIGNAL RULE ID IF Failed 
		try:
			resultQs = queryBuilder(searchTxt)
			for rq in resultQs:
				gramsInt = rq[0]
				queryStr = rq[1]
				# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
				#st.write('---- Querying ' + str(gramsInt) + '-gram DB for ' + queryStr)
				# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
				for g in gramsInt:
					df_selection = dfs[g].query(queryStr)
					if not df_selection.empty:
						if g not in resultDFs:
							resultDFs[g] = df_selection.sort_values('Norm',ascending=False)
						else:
							oldDF = resultDFs[g]
							resultDFs[g] = pd.concat([oldDF,df_selection], ignore_index=True).sort_values('Norm',ascending=False)
			#st.success('Successfully processed Rule ID# ' + str(ruleID))
		except:
			st.warning('Failed to process Rule ID# ' + str(ruleID))
		if len(resultDFs) > 0:
			# Add n-size column to each results table
			concatlist = []
			for g in resultDFs:
				resultDFs[g].insert(0,'N-size',str(g)+'-gram')
				concatlist.append(resultDFs[g])
			# concatenate results
			masterResultDF = pd.concat(concatlist)
			
			# add rule information columns in positions 0 and 1
			masterResultDF.insert(0,'Rule / Pattern',ruleLst[0])
			masterResultDF.insert(1,'Correction / Recommendation',ruleLst[1])
			masterResultDF.insert(2,'Rule ID',ruleID)
			
			outputResults.append(masterResultDF)
			
	if len(outputResults) > 0:
		outputDF = pd.concat(outputResults)
		# shift the score columns to the end
		outputDF.insert(len(outputDF.columns)-1, 'Norm', outputDF.pop('Norm'))
		outputDF.insert(len(outputDF.columns)-1, 'Scotus', outputDF.pop('Scotus'))
		outputDF.insert(len(outputDF.columns)-1, 'Good', outputDF.pop('Good'))
		outputDF.insert(len(outputDF.columns)-1, 'Random', outputDF.pop('Random'))
		outputDF.insert(len(outputDF.columns)-1, 'Gd.Rnd.Ratio', outputDF.pop('Gd.Rnd.Ratio'))

		return outputDF
	else:
		return pd.DataFrame()

def generateResults(ruleLst, ruleID):
	ruleDF0 = pd.DataFrame({'Rule / Pattern': ruleLst[0], 'Correction / Recommendation': ruleLst[1], 'Rule ID': [ruleID]})
	searchTxt = ruleLst[0]
	resultQs = queryBuilder(searchTxt)
	resultDFs = {}
	for rq in resultQs:
		gramsInt = rq[0]
		queryStr = rq[1]
		for g in gramsInt:
			df_selection = dfs[g].query(queryStr)
			if not df_selection.empty:
				if g not in resultDFs:
					resultDFs[g] = df_selection.sort_values('Norm',ascending=False)
				else:
					oldDF = resultDFs[g]
					resultDFs[g] = pd.concat([oldDF,df_selection], ignore_index=True).sort_values('Norm',ascending=False)
	# if using mongoDB loop through the dataframes and drop _id index column .drop('_id',axis=1,inplace=True)
	# dfDict_to_excel(resultDFs)
	if len(resultDFs) > 0:
		return dfDict_to_excel(ruleDF0, resultDFs)
	else:
		return None

def clear_resultsdir():
	dirpath = os.path.join(os.getcwd(),'results')
	for filename in os.listdir(dirpath):
		fpath = os.path.join(dirpath,filename)
		try:
			os.unlink(fpath)
		except Exception as e:
			print('Failed to delete %s. Exception: %s' % (fpath, e))

def runSubmit():
	clear_resultsdir()
	inRuleDict = {}
	resultFiles = {}
	if st.session_state['rule_file'] is None:
		st.warning('Please upload a valid rules file .xlsx')
	else:
		dfinrules=(pd.read_excel(load_file)).dropna(how='all')
		for index, row in dfinrules.iterrows():
			row_id = str(int(row['Rule ID']))
			row_rule = row['Rule / Pattern']
			if 'Correction / Recommendation' in dfinrules:
				row_correction = row['Correction / Recommendation']
			else:
				row_correction = ''
			inRuleDict[row_id] = [row_rule, row_correction]
		
		results_df = generateResultsAll(inRuleDict)
		st.success('Processing complete!')
		timestampStr = datetime.now().strftime("%Y%m%d_%H%M%S")
		if len(results_df.index) == 0:
			st.warning('No viable results!')
		else:
			df_xlsx_binary = df_to_excel(results_df)
			st.download_button('Download Results', data=df_xlsx_binary,file_name='results_'+timestampStr+'.xlsx')

# =====================================================================
# USER INTERFACE
# =====================================================================

st.header('BriefCatch Wizard :briefcase: :scales: :sparkles:')
st.markdown('---')

st.write('Upload Excel file containing at least one rule to analyze.  \nThe Excel table must include at least the following column names:  \n[[Rule / Pattern]] and [[Rule ID]] to proceed.')

load_file = st.file_uploader(label="",key='rule_file',accept_multiple_files=False, type=['.xlsx','.xls'])
submit = st.button('SUBMIT',key='submit_btn')
st.markdown('---')
col1, col2 = st.columns(2)


if submit:
	runSubmit()