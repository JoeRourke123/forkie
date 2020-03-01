import pymysql
from app import app
from db import mysql
from flask import Flask, Reponse, render_template

@app_route('/')
def upload_form()
    return render_template('download.html')

@app.route('/src/api/pdf/report')
def download_report():
    conn = None
    cursor = None
    try:
            conn = mysql.connect()
            cursor = conn.cursor(pymysql.cursors.DicCursor)

            #should be using postgresql

            cursor.execute("SELECT groupid, username, userID, email, groupname, groupleaderid FROM UserTable, GroupTable, UserGroupTable")
            result = cursor.fetchall()

            pdf = FPDF()
            pdf.add_page()

            page_width = pdf.w - 2 * pdf.l_margin

            pdf.set_font('Times' , 'B', 14.0)
            pdf.cell(page_width, 0.0, 'Group Report', align='C')
            pdf.ln(10)

            pdf.set_font('Courier', '', 12)

            col_width = page_width/4

            pdf.ln(1)

            th = pdf.font_size

            for row in result:
                pdf.cell(col_width, th, str(row['userID']), border=1)
                pdf.cell(col_width, th, row['username'], border=1)
                pdf.cell(col_width, th, row['email'], border=1)
                pdf.cell(col_width, th, row['groupid'], border=1)
                pdf.cell(col_width, th, row['groupname'], border=1')
                pdf.cell(col_width, th, row['groupleaderid'], border=1])
                pdf.ln(th)

            pdf.ln(10)

            pdf.set_font('Times','',10.0)
            pdf.cell(page_width, 0,0, '- end of report -', align='C')

            return Response(pdf.output(dest='S').encode('latin-1'), mimetype='application/pdf', headers={'Content-Disposition':'attachment;filename=group_report.pdf'})
        except Exception as e:
            print(e)
        finally:
            cursor.close()
            conn.close()
if __name__ == "__report__":
    app.run()
