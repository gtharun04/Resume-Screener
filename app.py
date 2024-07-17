# Import libraries

import streamlit as st
import pandas as pd
import numpy as np
import time
import google.generativeai as genai
import PyPDF2 as pdf
from docx import Document
import io
from dotenv import load_dotenv



# Configure LLM with Gemini Key

load_dotenv()

# genai.configure(api_key = ('GOOGLE_API_KEY'))
genai.configure(api_key='AIzaSyBuinM21k9mshd-YQy7y_eHinclhDry-PY')

# User Define Functions

def get_gemini_response(input):
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content(input)
    return response.text

def extract_text_from_file(uploaded_file):
  
    filename = uploaded_file.name
    extension = filename.split('.')[-1].lower()

    text = ""

    if extension == 'pdf':
        pdf_bytes = uploaded_file.read()
        pdf_file = io.BytesIO(pdf_bytes)
        reader = pdf.PdfReader(pdf_file)

        for page in reader.pages:
            text += page.extract_text()

        pdf_file.close()

    elif extension == 'docx':
        docx_file = uploaded_file.read()
        doc = Document(io.BytesIO(docx_file))
        for paragraph in doc.paragraphs:
            text += paragraph.text

    else:
        print(f"Unsupported file format: {extension}")

    return text

# Prompt to match resumes to JD

input_prompt_2 = """
You are an HR executive of a company and your role is to match the candidates resumes to the Job Description provided.
You need to look for the skills needed in the Job Description and judge if the specific resume is a good match and determine the percentage of match.
Recent role should be the last working role in the experience section.
Total Experience should be the sum of all the periods working for a company in experience section.
In experience section there might be more than one company so consider all the individual companies as work experience and sum all of them and make sure to specify exact number.
Highest Qualification should be the latest education in the resume.
Skills must be extracted from the skills section. Do not keep it empty. Srictly list only the important skills within 20 words.
Summary should be brief in 30 words
If you do not find any information return as 'Information Not Found'. Do check the information again if it is available before judging as 'Information not found' 
Consider the inputs here:
Job Description: {JD}
Resume:{text}

The output should be in this format and mention skills in a single straight line:
Candidate Name:
Matching Percentage:
Matching Skills:
Contact Number:
Email id:
Highest Qualification:
Recent Role:
Total years of experience:
Summary of the resume:

"""

# Set app title
st.set_page_config(page_title="Resume Screener", layout="wide")

# Create containers for horizontal alignments

container1 = st.container()
container2 = st.container()


# Create columns for vertical alignments

col3,col4 = st.columns([1.5,4])

image = col3.image("images.png", width=200)
col4.write('<h1 style="color: green;margin-top:5px;">Reboot @ Lloyds Technology Center</h1>', unsafe_allow_html=True)


st.write('<h1 style="color: black; width: 10000px;padding:0px;">Resume Scanner</h1>', unsafe_allow_html=True)

col1, col2 = st.columns([2.8,1])

container3 = st.container()

# This container has Job Description and Upload Resumes styling
with container1: 
    # Style for Job Description text area
    st.write('<style>.st-bp { font-size: 14px; padding: 0px; gap:0px;} /* Adjust styles as needed */</style>', unsafe_allow_html=True)
    job_description = col1.text_area("Enter Your Job Description", key="job_description", height = 300)

    uploaded_files = col2.file_uploader("Upload Resumes", type=['pdf', 'docx'], accept_multiple_files =True)  # Adjust file types as needed
    upload_clicked = col2.button("Upload")
    
    if uploaded_files and upload_clicked:  # Check both conditions
        progress_bar = col2.progress(0)
        for perc_completed in range(100):
            time.sleep(0.01)
            progress_bar.progress(perc_completed + 1)

        col2.success('Resumes have been uploaded ')

# This container starts the process once the Analyze is clicked
with container2: 
    analyze_clicked = col1.button("Analyze")
    if analyze_clicked:
        start_time = time.perf_counter()

        JD_text = job_description

        # Main loop to get the data from LLM
        data = []

        progress_text = col1.empty()
        progress_bar = col1.progress(0)
        loop_counter = 0

        def update_progress(loop_counter, total_resumes):
            return f"Processed {loop_counter} out of {total_resumes} resumes"
        # Passing each resume through the loop
        for CV_file in uploaded_files:
            # print('CV Looped all')
            print(CV_file.name)
            CV_text = extract_text_from_file(CV_file)
            print(CV_text)

            formatted_prompt = input_prompt_2.format(text=CV_text,JD=JD_text)
            response = get_gemini_response(formatted_prompt)  
            # print(response)
            # Splitting the response generated by the LLM          
            response_lines = response.split('\n')
            info = {
                "File Name" : CV_file.name,
                "Candidate Name": "Information Not Found",
                "Matching Percentage": "Information Not Found",
                "Matching Skills":"Information Not Found",
                "Contact Number":"Information Not Found",
                "Email id":"Information Not Found",
                "Highest Qualification":"Information Not Found",
                "Recent Role":"Information Not Found",
                "Total years of experience":"Information Not Found",
                "Summary of the resume":"Information Not Found",
            }
            # Assigning it to the specific columns
            for line in response_lines:
                # if "File Name:" in line:
                #     info["File Name"] = line.split(":", 1)[1].strip()
                if "Candidate Name:" in line:
                    info["Candidate Name"] = line.split(":", 1)[1].strip()
                elif "Matching Percentage:" in line:
                    info["Matching Percentage"] = line.split(":", 1)[1].strip()
                elif "Matching Skills:" in line:
                    info["Matching Skills"] = line.split(":", 1)[1].strip()
                elif "Contact Number:" in line:
                    info["Contact Number"] = line.split(":", 1)[1].strip()
                elif "Email id:" in line:
                    info["Email id"] = line.split(":", 1)[1].strip()
                elif "Highest Qualification:" in line:
                    info["Highest Qualification"] = line.split(":", 1)[1].strip()
                elif "Recent Role:" in line:
                    info["Recent Role"] = line.split(":", 1)[1].strip()
                elif "Total years of experience:" in line:
                    info["Total years of experience"] = line.split(":", 1)[1].strip()
                elif "Summary of the resume:" in line:
                    info["Summary of the resume"] = line.split(":", 1)[1].strip()
                
            data.append(info)
            loop_counter += 1
            progress_bar.progress(int(loop_counter / len(uploaded_files) * 100))
            progress_text.text(update_progress(loop_counter, len(uploaded_files)))

        end_time = time.perf_counter()
        elapsed_time = end_time - start_time
        col1.success(f"Hola! Finished the analysis in {elapsed_time:.2f} seconds")

        # Transforming the data into a dataframe
        df = pd.DataFrame(data)
        print(df)
        # df = df.sort_values(by='File Name')
        styles = """
                    td {
                        max-width: 0px;
                        overflow: hidden;
                        text-overflow: ellipsis;
                        white-space: nowrap;
                        color: black;
                        background-color: beige;
                        border-radius: 5px;
                    }

                    th {
                        background-color: lightseagreen;
                        font-weight: bold;
                    }

                    table {
                        width: 40%;
                        border-radius: 5px;
                    }
                    """
        # This container is for the table
        with container3: 

            # with open('styles.css') as f:
            #     st.markdown(f'<style>{f.read()}</style>',unsafe_allow_html=True)
            st.markdown(f'<style>{styles}</style>', unsafe_allow_html=True)

            st.table(df)
            timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")

            # download_clicked = st.button('Download')
            st.download_button("Download CSV", df.to_csv(), mime='text/csv', file_name= (f"matching_score_{timestamp}.csv"))




# Unused Code
        # transposed_df = df.T.to_numpy()  # Transpose and convert to NumPy array
        # column_names = [f"<b>{name}</b>" for name in df.columns]
        # fig = go.Figure(data = go.Table(
        #     header = dict(values = column_names,
        #                 fill_color = 'seagreen'
        #                 ),
        #     cells=dict(values=transposed_df.tolist(),  # Convert NumPy array to list

        #                 fill_color = 'lightgray',
        #                 align = 'left')
        #     )
        #     )