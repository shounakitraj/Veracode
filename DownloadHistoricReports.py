import os
import sys
import requests
from xml.etree import ElementTree
from veracode_api_signing.plugin_requests import RequestsAuthPluginVeracodeHMAC

sandbox_name = 'SANDBOX NAME'
api_base = "https://analysiscenter.veracode.com/api/5.0"
pdf_api_base = "https://analysiscenter.veracode.com/api/4.0"
veracode_headers = {"User-Agent": "Python HMAC Example"}
pdf_filepath = "/home/developer/veracode_reports"


def GetAppId(application_name="APPLICATION NAME"):
    for i in range(3):
        try:
            response = requests.get(api_base + "/getapplist.do", auth=RequestsAuthPluginVeracodeHMAC(),
                                    headers=veracode_headers)
            break
        except Exception as e:
            print(str(e) + ": Error caused for getapplist.do API")
    application_list = ElementTree.fromstring(response.content)
    for list in application_list:
        if list.attrib['app_name'] == application_name:
            return list.attrib['app_id']
    print("Could not find Application id exiting the program")
    sys.exit(1)


def GetSandboxId(app_id, sandboxname):
    for i in range(3):
        try:
            response = requests.get(api_base + "/getsandboxlist.do?app_id=%s" % app_id,
                                    auth=RequestsAuthPluginVeracodeHMAC(),
                                    headers=veracode_headers)
            break
        except Exception as e:
            print(str(e) + ": Error caused for getsandboxlist.do API")

    sandbox_list = ElementTree.fromstring(response.content)
    for list in sandbox_list:
        if list.attrib['sandbox_name'] == sandboxname:
            return list.attrib['sandbox_id']
    print("Could not find sandbox id exiting the program")
    sys.exit(1)


def GetBuildsData(app_id, sandbox_id):
    buildlist = []
    for i in range(3):
        try:
            response = requests.get(api_base + "/getbuildlist.do?app_id=%s&sandbox_id=%s" % (app_id, sandbox_id),
                                    auth=RequestsAuthPluginVeracodeHMAC(),
                                    headers=veracode_headers)
            break
        except Exception as e:
            print(str(e) + ": Error caused for getbuildlist.do API")
    buidlist = ElementTree.fromstring(response.content)
    for i in reversed(buidlist):
        for j in range(3):
            try:
                response = requests.get(
                    api_base + "/getbuildinfo.do?app_id=%s&build_id=%s&sandbox_id=%s" % (
                        app_id, i.attrib['build_id'], sandbox_id),
                    auth=RequestsAuthPluginVeracodeHMAC(),
                    headers=veracode_headers)
                break
            except Exception as e:
                print(str(e) + ": Error caused for getbuildinfo.do API")
        buildinfo = ElementTree.fromstring(response.content)
        for k in buildinfo:
            if k.attrib['results_ready'] == 'true':
                buildlist.append(i.attrib['build_id'])
    print("Total builds: %d" %len(buildlist))
    return buildlist

try:
    # Get app id
    app_id = GetAppId()

    # Get sandbox id
    sandbox_id = GetSandboxId(app_id, sandbox_name)

    # Get build id
    buildlist = GetBuildsData(app_id, sandbox_id)

    if len(buildlist) == 0:
        print("Did not get any list of build")
        sys.exit(1)
    for i in range(len(buildlist)):
        response = requests.get(api_base + "/detailedreport.do?build_id=%d" % int(buildlist[i]),
                                auth=RequestsAuthPluginVeracodeHMAC(), headers=veracode_headers)
        detailed_report = ElementTree.fromstring(response.content)
        report_date = detailed_report[0].attrib['published_date'].split(" ")[0]
        response = requests.get(pdf_api_base + "/detailedreportpdf.do?build_id=%s" % buildlist[i],
                                auth=RequestsAuthPluginVeracodeHMAC(), headers=veracode_headers)
        pdf_file = 'Veracode_Scan_%s.pdf' % report_date
        report_file = os.path.join(pdf_filepath, pdf_file)
        with open(report_file, 'wb') as f:
            f.write(response.content)

except Exception as e:
    print(e)