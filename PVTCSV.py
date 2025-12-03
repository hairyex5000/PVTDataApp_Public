# pylint: skip-file
import pandas as pd
import streamlit as st
import tempfile
import uuid

from sheets import SheetsDataHandler

ROOT_URL = st.secrets.root_url

class CustomError(ValueError):
    pass

class CombinedDataTable:
    def array_agg(self, data: pd.Series, *args):
        if data.index.size > 1:
            return data.min()
        elif data.index.size == 1:
            return data.iloc[0]
        return ""

    def __init__(self, pvt: pd.DataFrame, survey: pd.DataFrame):
        print(pvt)
        try:
            survey = survey[survey.index.str.startswith("FS_")]
        except:
            raise CustomError('The survey file was invalid.')
        try:
            pvt['datetime'] = pd.to_datetime(pvt['datetime'])
            pvt = pvt.groupby('sessionID').agg(lambda x: self.array_agg(x))
            pvt['datetime'] = pvt['datetime'].astype(str)
        except:
            raise CustomError('The PVT file was invalid.')
        try:
            self.combined = survey.join(other=pvt, how='inner')
            self.missing_survey = survey[~survey.index.isin(self.combined.index.to_list())]
            self.missing_pvt = pvt[~pvt.index.isin(self.combined.index.to_list())]
            self.download = self.output_excel_raw()
        except:
            raise CustomError('A error occured when combining the files. Check to make sure you have the right files uploaded.')

    def output_file(self, file_name: str = "combined.csv"):
        self.combined.to_csv(file_name)

    def output_excel_raw(self):
        with tempfile.SpooledTemporaryFile(max_size=10000*1000) as tmp:
            self.combined.to_excel(tmp, sheet_name="combined_data")
            tmp.seek(0)
            return tmp.read()

def from_file(pvtFileName = "pvt.csv", surveyFileName = "survey.csv", pvtType = "csv", surveyType = "csv"):
    tmp_pvt = None
    tmp_survey = None
    if pvtType == "csv":
        tmp_pvt = pd.read_csv(pvtFileName)
    elif "xls" in pvtType:
        tmp_pvt = pd.read_excel(pvtFileName)
    elif isinstance(pvt_file, pd.DataFrame):
        tmp_pvt = pvt_file
    if surveyType == "csv":
        tmp_survey = pd.read_csv(surveyFileName)
    else:
        tmp_survey = pd.read_excel(surveyFileName)
    try:
        tmp_pvt = tmp_pvt.set_index("sessionID")
    except:
        st.warning("The PVT file was invalid.")
        return None
    try:
        tmp_survey = tmp_survey.rename(columns={"SessionID": "sessionID"}).set_index("sessionID")
    except:
        st.write("The survey file was invalid.")
    return CombinedDataTable(tmp_pvt, tmp_survey)


if 'logout' in st.query_params.to_dict() and st.query_params['logout'] == 'yes':
    st.logout()
elif 'is_logged_in' in st.user.to_dict() and st.user.is_logged_in:
    # st.html(f'''
    # <a href='https://dev-l3hwkecdz1em3uww.us.auth0.com/oidc/logout?post_logout_redirect_uri={ROOT_URL}/?logout=yes' target='_top'><button>Log Out</button></a>
    # ''')
    st.page_link(page=f'https://dev-l3hwkecdz1em3uww.us.auth0.com/oidc/logout?post_logout_redirect_uri={ROOT_URL}/?logout=yes', label="Log Out")
    st.sidebar.write("Upload Files")
    pvt_file = None
    if st.sidebar.radio("PVT Data Source", options=['File', 'Google Sheets']) == 'Google Sheets':
        pvt_file = SheetsDataHandler().get_pvt_data()
    else:
        pvt_file = st.sidebar.file_uploader(label="PVT Data", type=['csv', 'xls', 'xlsx'])

    survey_file = st.sidebar.file_uploader(label="Survey Data", type=['csv', 'xls', 'xlsx'])

    if (pvt_file is not None) and (survey_file is not None):
        try:
            if not isinstance(pvt_file, pd.DataFrame):
                pvtobj = from_file(pvt_file, survey_file, str(pvt_file.name).split(".")[-1], str(survey_file.name).split(".")[-1])
            else:
                pvtobj = from_file(pvt_file, survey_file, "df", str(survey_file.name).split(".")[-1])

        except CustomError as error:
            st.warning(str(error))
            pvtobj = None
        if pvtobj is not None:
            basic_column_view = ["RecordedDate", "RecipientLastName", "RecipientFirstName", "RecipientEmail", "Finished"]

            acol1, acol2 = st.columns(2)
            st.write("Combined Data Table")

            with acol1:
                option = st.radio("Data View Options", options=["Basic", "Extended"])
            with acol2:
                st.download_button("Download Combined Table", data=pvtobj.download, file_name=str(uuid.uuid4())+".xlsx")
            if option == "Extended":
                st.dataframe(pvtobj.combined)
            else:
                st.dataframe(pvtobj.combined[basic_column_view])

            st.write("Missing Values")

            bcol1, bcol2 = st.columns(2)
            with bcol1: # if it is not in one, then it is in the other
                st.write("Missing Survey Data")
                st.dataframe(pvtobj.missing_pvt['contactID'])
            with bcol2:
                st.write("Missing PVT Data")
                st.dataframe(pvtobj.missing_survey['ContactID'])
    else:
        st.write("Upload the files using the sidebar.")
else:
    st.login()