import requests, csv
from bs4 import BeautifulSoup
import s3cookiejar, mechanize
import pandas as pd
import time


'''
Author: Jack C. Gee
'''
#########################################################


def holly_complete_check(expNum):
    '''
    should check the passed exp num to see if complete_formulations == total_formulations before proceeding if =/= sleep for 5 mins?
    if sleeping print time of sleep start and duration to show its not crashed
    '''
    print("Checking Exp. " + expNum)
    cj = s3cookiejar.S3CookieJar()
    br = mechanize.Browser()
    br.set_cookiejar(cj)
    br.open("http://138.253.226.89/RobotRun")
    br.select_form(nr=0)
    br.form['UserName'] = 
    br.form['Password'] = 
    br.form['CompanyId'] = ["1",] #1 labman, 2 UoL, 3 Unilever
    br.submit()

    print("Logging in")

    br.open("http://138.253.226.89/Experiment/ViewExperiment/" + expNum)
    html = br.response().read()
    soup = BeautifulSoup(html, 'html.parser')

    divs = soup.find_all("div", class_= "col-md-8 divborder")
    '''strips webpage to classes
    divs[0] is exp details
    divs[1] is exp stats ---- this is the important one
    etc.
    '''
    exp_stats = str(divs[1]) # needs str else is nonetype
    exp_stats = exp_stats.splitlines()
    total_forms = exp_stats[2]
    total_forms = (total_forms.split("</b>"))[1]
    total_forms = (total_forms.split("<br/>"))[0]
    total_forms = total_forms.strip()

    comp_forms = exp_stats[3]
    comp_forms = (comp_forms.split("</b>"))[1]
    comp_forms = (comp_forms.split("<br/>"))[0]
    comp_forms = comp_forms.strip()

    if comp_forms == total_forms:
        print("Exp: " + expNum + " ready for processing")
        return True
    else:
        print("Exp: " + expNum + " not ready")
        return False

def holly_webscaper(expNum):
    print("Attempting to scrape")
    cj = s3cookiejar.S3CookieJar()
    br = mechanize.Browser()

    br.set_handle_robots(False)  # no robots
    br.set_handle_refresh(False)
    br.addheaders = [('User-agent',
                      'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1')]
    # [('User-agent', 'Firefox')]
    br.set_cookiejar(cj)  # allow everything to be written to

    #logs in to holly
    br.open("http://138.253.226.89/RobotRun")
    br.select_form(nr=0)
    br.form['UserName'] = 'livad\mif015'
    br.form['Password'] = 'emsfl0w1'
    br.form['CompanyId'] = ["1",] #1 labman, 2 UoL, 3 Unilever
    br.submit()

    print("Logging in")

    #expNum = "665"
    #expNum = data
    print("exp num :" + expNum)
    #br.follow_link("http://138.253.226.89/RobotRun/ViewRobotRun/"+robotRun)
    br.open("http://138.253.226.89/Experiment/ViewExperiment/"+expNum)
    #br._factory.is_html = True
    html = br.response().read()
    soup = BeautifulSoup(html, 'html.parser')
    #print(soup.prettify())
    # br.open("http://138.253.226.89/RobotRun")
    # br.select_form(nr=0)
    # print(br.form)


    #page = requests.get("http://138.253.226.89/RobotRun")


    #print(soup.find_all('tr'))
    # for tr in soup.find_all('tr'):
    #     tds = tr.find_all('td')
    # print(tds)

    table = soup.find(lambda tag: tag.name=='table' and tag.has_attr('id') and tag['id']=="formulationsTable")
    rows = table.findAll(lambda tag: tag.name=='tr')


    formulationsDict = {}
    dispenseDict = {}
    print("Scraping Exp. {}".format(expNum))
    #finds all formulationIDs in exp and their status
    for row in rows[1:]:
        row = str(row)
        row = row.splitlines(True)

        form_id = row[2]
        form_id = form_id.split("<label>")
        form_id = form_id[1].split("</label>")
        form_id = form_id[0]

        form_name = row[5]
        form_name = form_name.split("<label>")
        form_name = form_name[1].split("</label>")
        form_name = form_name[0]

        form_status = row[14]
        if "Complete" in form_status:
            form_status = "Complete"
        if "Error" in form_status:
            form_status = "Error"
        if "Processing" in form_status:
            form_status = "Processing"

        formulationsDict.setdefault("form_id", []).append(form_id)
        formulationsDict.setdefault("form_name", []).append(form_name)
        formulationsDict.setdefault("form_status", []).append(form_status)

    formulation_df = pd.DataFrame.from_dict(data=formulationsDict)
    formulation_df.set_index('form_id', inplace=True)

    #goes through each formulation for dispense amounts

    print("got form_ids, getting dispenses")
    form_list = []
    form_dict_list = []
    dispense_dict_list = []
    dictionary = {}
    end_dict_list=[]
    length = len(formulationsDict["form_id"])
    counter = 1
    for i in formulationsDict["form_id"]:
        while True:
            try:
                print("Processing: "+str(counter)+"/"+str(length))
                br.open("http://138.253.226.89/Experiment/ViewFormulation/"+i)
                html = br.response().read()
                soup = BeautifulSoup(html, 'html.parser')
                #simplistic workaround as both tables on this page have the same unique ID
                table = soup.find_all('table')[1]
                rows = table.findAll(lambda tag: tag.name == 'tr')
                material_list = []
                act_amount_list = []
                form_list.append(i)
                #dictionary.setdefault("form_id", []).append(i)
                #dispenseDict.setdefault("form_id", []).append(i)
                end_dict=[]
                for row in rows[1:]:
                    row = str(row)
                    row = row.splitlines(True)
                    instruc = row[2]
                    material = None
                    act_amount = None
                    if "IngredientAddition" in instruc:
                        material = row[12]
                        material = material.split("</td>")
                        material = material[0].strip()

                        # tar_amount = row[13]
                        # tar_amount = tar_amount.split("<td>")
                        # tar_amount = tar_amount[1].split("</td>")
                        # tar_amount = tar_amount[0]

                        act_amount = row[15]
                        if "good" in row[15]:
                            act_amount = act_amount.split('<td class="good">')
                            act_amount = act_amount[1].split("</td>")
                            act_amount = act_amount[0]
                            material_list.append(material)
                            act_amount_list.append(act_amount)
                        elif "warning" in row[15]: # discounts the yellow labelled dispenses - likely 0?
                            continue
                counter += 1
                break
            except Exception as e:
                print(e)
                print("Retrying in 5s")
                time.sleep(5)
                continue


        dispense_dict = dict(zip(material_list, act_amount_list))
        '''packs the dispense data for easier unloading into dataframe'''

        #dispense_dict = [dispense_dict]

                #amountList.append(act_amount)
                #dispenseDict.setdefault("form_id", []).append(i)
                #materialList =
                #dispenseDict = {i: {material: act_amount}}
                #dispenseDict.setdefault(i, []).append(material)
                #dispenseDict.setdefault(i, []).append(act_amount)


        #dispenseDict.setdefault("dispenses", []).append(dispense_dict)
        #dispenseDict.setdefault("form_id", i).setdefault("dispenses", []).append(dispense_dict)

    # for id in form_list:
    #     form_dict = {"form_id" : id}
    #     form_dict_list.append(form_dict)



        end_dict = {i:dispense_dict}
        end_dict_list.append(end_dict)

    #print(end_dict)

        #https: // www.geeksforgeeks.org / python - convert - list - of - nested - dictionary - into - pandas - dataframe /

        #dict = [{"form_id":1, "dispsenses":[{"cat":0.005, "water": 5}, {"cat":0.005, "water":5}]}]

        #dispenseList.append(dispenseDict)





    #dispenses_df = pd.concat({k: pd.DataFrame(v) for k, v in dispenseDict.items()}, axis=0)

    #pd.DataFrame(dispenseDict)

    # rows list initialization
    rows = []
    # appending rows
    #print(dispenseList)

    '''takes the end dictionary list of mat names and dispense amounts and puts into df with form id as index'''
    for data in end_dict_list:
        for i in data:
            id = i
        #time = data["form_id"]
        data_row = data.values()
        #print(data_row)

        for row in data_row:
            row["form_id"] = id
            rows.append(row)

        # using data frame
    dispenses_df = pd.DataFrame(rows)
    dispenses_df.set_index("form_id", inplace=True)
    #print(dispenses_df)
    # print(df)

     # dispenses_df = pd.DataFrame.from_dict({(i): dispenseDict[i]
     #                            for i in dispenseDict.keys()
     #                            for j in dispenseDict[i]},
     #                        orient='index')

    #dispenses_df = pd.DataFrame.from_dict(data=dispenseDict)
    #dispenses_df = dispenses_df.transpose()



    #print(dispenses_df)

    #formulation_dispenses_df= formulation_df.merge(dispenses_df, left_on="form_id")
    formulation_dispenses_df = pd.concat([formulation_df, dispenses_df], axis=1, sort=True)
    #formulation_dispenses_df.set_index("form_id", inplace=True)
    #print(formulation_dispenses_df)
    print("Scraping complete")
    return formulation_dispenses_df
    #formulation_dispenses_df.to_csv("F:\DOWNLOADS (HDD)\csv.csv")

    #formulation_dispenses_df.loc[i] = [material] + [act_amount]

           #print(row(2,13,14,15,16))
    # print(dispenseDict)

    #all_products = []

    #products = soup.select('div.thumbnail')


    #first_h1 = soup.select('h1')

    # with open('products.csv', 'w', newline='') as output_file:
    #     dict_writer = csv.DictWriter(output_file, keys)
    #     dict_writer.writeheader()
    #     dict_writer.writerows(all_products)
