import streamlit as st
import pandas as pd
import numpy as np
from pyxlsb import open_workbook as open_xlsb
from io import BytesIO
st.title("ISERVEU RECON PROCESS")
Mware = st.file_uploader('mware a file containing m/w data')
Npci = st.file_uploader('npci a file containing npci data')
Switch=st.file_uploader('switch a file containing switch data')
mware=pd.read_excel(Mware)
npci=pd.read_excel(Npci)
switch=pd.read_excel(Switch)
# import streamlit as st
# import pandas as pd
# import numpy as np
# mware = pd.read_excel(r'NSDL AEPS MIDDLEWARE FILE - 24-10-2022.xlsx')
# # print(mware)
# npci = pd.read_excel(r'NSDL AEPS NPCI FILE - 24-10-2022.xlsx')
# # print(npci)
# switch = pd.read_excel(r'NSDL AEPS SWITCH FILE - 24-10-2022.xlsx')
# print(switch)
#MIDDILE WARE

mware_new = mware[['apiTid', 'operationPerformed', 'status', 'amountTransacted', 'createdDate', 'transactionMode', 'cardDetails', 'userName']]
mware_new.rename(columns={'cardDetails': 'Card No', 'apiTid': 'RRN', 'operationPerformed': 'Transaction Type',
                          'status': 'Transaction Status', 'amountTransacted': 'Transaction Amount',
                          'createdDate': 'Transaction Date Time', 'userName':'Username'}, inplace=True)
mware_new.loc[mware_new['Transaction Type'] == 'mATM_CASH_WITHDRAWAL', 'Transaction Type'] = 'cash withdrawal'
mware_new.loc[mware_new['Transaction Type'] == 'mATM_MINI_STATEMENT', 'Transaction Type'] = 'mini statement'
mware_new.loc[mware_new['Transaction Type'] == 'mATM_BALANCE_ENQUIRY', 'Transaction Type'] = 'balance enquiry'
# print("BEFORE MERGE MWARE DATA:",mware)
# NPCI
npci_new = npci[
    ['TransactionSerialNumber', 'Transaction Type', 'Response Code', 'Actual Transaction Amount', 'Transaction Date',
     'PAN Number', 'Card Acceptor Term. Location']]
npci_new.rename(
    columns={'PAN Number': 'Card No', 'TransactionSerialNumber': 'RRN', 'Transaction Type': 'Transaction Type',
             'Response Code': 'Transaction Status', 'Actual Transaction Amount': 'Transaction Amount',
             'Transaction Date': 'Transaction Date Time'}, inplace=True)
npci_new['Transaction Status'] = np.where(npci_new['Transaction Status'] == '00', 'SUCCESS', 'FAILED')
npci_new.loc[npci_new['Transaction Type'] == 4, 'Transaction Type'] = 'cash withdrawal'
# npci_new.loc[npci_new['Transaction Type'] == 7, 'Transaction Type'] = 'mini statement'
npci_new.loc[npci_new['Transaction Type'] == 5, 'Transaction Type'] = 'balance enquiry'
npci_new[['Username','Card Acceptor Term. Location']] = npci_new['Card Acceptor Term. Location'].str.split(n=1, expand=True)
# print("BEFORE MERGE NPCI DATA:",npci)
# SWITCH
switch_new = switch[['RRN', 'transaction_type', 'response_code', 'transaction_amount', 'Date',
                     'Card Number (Masked)', 'Card acceptor name / location']]
switch_new.rename(columns = {'Card Number (Masked)': 'Card No', 'transaction_amount': 'Transaction Amount', 'transaction_type':'Transaction Type', 'response_code':'Transaction Status'}, inplace=True)
switch_new.loc[switch_new['Transaction Type'] == 'Cash Withdrawal.', 'Transaction Type'] = 'cash withdrawal'
# switch_new.loc[switch_new['Transaction Type'] == 'Offus Mini Statement', 'Transaction Type'] = 'mini statement'
switch_new.loc[switch_new['Transaction Type'] == 'Balance Enquiry.', 'Transaction Type'] = 'balance enquiry'
switch_new['Transaction Status'] = np.where(switch_new['Transaction Status'] == '00', 'SUCCESS', 'FAILED')
switch_new[['Username','Card Acceptor Term. Location']] = switch_new['Card acceptor name / location'].str.split(n=1, expand=True)
print(switch_new['Transaction Status'].value_counts())
# print("BEFORE MERGE SWITCH",switch)
mware_new['Card No New'] = mware_new['Card No'].str[-4:]
# # switch_new['Card No'] = switch_new['Card No'].astype(str)
switch_new['Card No'].apply(str).str.replace(',', '')
switch_new['Card No New'] = switch_new['Card No'].str[-4:]
npci_new['Card No'] = npci_new['Card No'].astype(str)
npci_new['Card No New'] = npci_new['Card No'].apply(lambda x: x[-4:])
# MERGE
print(mware_new.info())
print(switch_new.info())
print(npci_new.info())
df_merge = pd.merge(pd.merge(npci_new, switch_new, on='RRN', how='outer', suffixes=("_npci", "_switch")), mware_new,
                    on='RRN', how='outer')
# list of column matches
column_match1 = ['Transaction Status', 'Transaction Amount', 'Transaction Type', 'Card No New', 'Username']
# match of three excel sheet of this column
for key in column_match1:
    df_merge['{}_final_status'.format(key)] = df_merge[['{}_switch'.format(key), '{}_npci'.format(key)]].eq(
        df_merge['{}'.format(key)], axis=0).all(axis=1)
    df_merge['{}_final_status'.format(key)] = np.where(df_merge['{}_final_status'.format(key)] == 0, '{} '.format(key),
                                                       '')
print("2 column merge report 3excel sheet::", df_merge)
# column_match2 = ['Transaction Type']
# #list of column matches in 2 excel sheet
# for key in column_match2:
#     df_merge['{}_final_status'.format(key)] = np.where((df_merge['{}_switch'.format(key)] == df_merge['{}_npci'.format(key)]),'{} '.format(key), '' )
# match1 AND match2 concatenate
# column_match = column_match1 + column_match2
# this will print the why column not matched
df_merge['final_status_description'] = ''
for key in column_match1:
    df_merge['final_status_description'] += df_merge['{}_final_status'.format(key)]
df_merge['final_status'] = ''
# this list for the match or mismatch
df_merge['final_status'] = np.where(df_merge['final_status_description'] == '', 'Match', 'Mismatch')
for key in column_match1:
    del df_merge['{}_final_status'.format(key)]
df_merge['Transaction Sector'] = ''
df_merge['Transaction Sector'] = np.where(df_merge['Transaction Type_npci'] == 'cash withdrawal', 'Financial', 'Non-financial')
df_merge.loc[df_merge['Transaction Type_npci'].isnull(), 'Transaction Sector'] = 'not updated'
print("MATCH COUNT:", df_merge['final_status'].value_counts())
print("final status:::", df_merge['final_status'])
print("merge columns:", df_merge.columns)
mware.rename(columns={ 'apiTid': 'RRN', 'transactionMode': 'Transaction Type',
                      'status': 'Transaction Status', 'amountTransacted': 'Transaction Amount',
                      'createdDate': 'Transaction Date Time'}, inplace=True)
npci.rename(
    columns={'TransactionSerialNumber': 'RRN', 'Transaction Type': 'Transaction Type',
             'Response Code': 'Transaction Status', 'Actual Transaction Amount': 'Transaction Amount',
             'Transaction Date': 'Transaction Date Time'}, inplace=True)
df_final = pd.merge(pd.merge(npci, switch, on='RRN', how='outer', suffixes=("_npci", "_switch")), mware, on='RRN',
                    how='outer')
df_final.index = df_merge.index
df_final['final status'] = df_merge['final_status']
df_final['final_status_description'] = df_merge['final_status_description']
df_final['Transaction Sector'] = df_merge['Transaction Sector']
df_final.to_csv('alldata.csv')
df_merge.to_csv('mergedata.csv')
st.write(df_merge['final_status'].value_counts())
df_merge.to_csv(index=False).encode('utf-8')
df_final.to_csv(index=False).encode('utf-8')
# st.download_button("Download CSV",df_merge.to_excel,file_name='Recon_file.csv',mime='text/csv')
# st.sidebar.download_button(label='Download CSV',data=result,mime='text/csv',file_name='Download.csv')
def to_excel(df):
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, index=False, sheet_name='Sheet1')
    workbook = writer.book
    worksheet = writer.sheets['Sheet1']
    format1 = workbook.add_format({'num_format': '0.00'}) 
    worksheet.set_column('A:A', None, format1)  
    writer.save()
    processed_data = output.getvalue()
    return processed_data
df_xlsx = to_excel(df_merge)
# df_xlsx=b'df_merge'
st.download_button(label='📥 Download Recon Result',
                                data=df_xlsx ,
                                file_name= 'ippbmatmrecon.xlsx')

df_xlsx = to_excel(df_final)
# df_xlsx=b'df_merge'
st.download_button(label='📥 Download All mergedata Result',
                                data=df_xlsx ,
                                file_name= 'alldataippbmatmrecon.xlsx')
