#*------------ Imports ------------*#

from __future__ import print_function
# This is an essential import for the GDrive API
from apiclient import discovery
from httplib2 import Http
from oauth2client import file, client, tools
from datetime import datetime
import math

from datetime import datetime
from dateutil.relativedelta import relativedelta, FR


#*------------ Vars ------------*#
# these two files need to be generated by you with your api keys and
# secrets in them.
CREDS_FILE = 'client_secret.json'
STORAGE_FILE = 'storage.json'
# Id to my Google Sheet doc
# This step really isn't needed, since I would have been just as well
# off making an Airtable API call to get this data.. 
DATA_SHEET_ID = '1kOQqmrTgYoUVaT0Giz-henDajHW4JR8z5XztWUsK228'
# In my case, I need to populate three different template slides with different
# bits of data. These are the IDs of those three templates in my slide template
# doc.
DOMAIN_REPORT_SLIDE_ID = 'g3530d0b958_1_394'
RISKS_REPORT_SLIDE_ID = 'g374ce3ef54_0_264'
MILESTONES_REPORT_SLIDE_ID = 'g374ce3ef54_0_229'


# First designer element index on the slides is '19'
# and there are 9 desiger placeholder elements
DESIGNER_PLACEHOLDER_OFFSET = 19
DESIGNER_PLACEHOLDERS = 9
PROJECT_TITLE_CHARACTER_MAX = 45
PROJECT_DESCRIPTION_CHARACTER_MAX = 250
TEMPLATE_RED = {'red': 0.82, 'green': 0.19, 'blue': 0.15}
TEMPLATE_BLUE = {'red': 0.13, 'green': 0.45, 'blue': 0.69}
TEMPLATE_GREEN = {'red': 0.05, 'green': 0.68, 'blue': 0.05}
TEMPLATE_YELLOW = {'red': 0.97, 'green': 0.80, 'blue': 0.00}
PROGRESS_BAR_GRAY = {'red': 0.41, 'green': 0.46, 'blue': 0.50}
TEMPLATE_DARK_GRAY = {'red': 0.50, 'green': 0.46, 'blue': 0.41}
RISK_COLORS_ARRAY = [TEMPLATE_GREEN, TEMPLATE_YELLOW, TEMPLATE_RED]
SELECTOR_DOT_POSITIONS = [
                            [671135.145, 2],
                            [1289623.485, 3],
                            [2045030.6649999998, 4],
                            [2817574.6275, 5],
                            [3575186.1025, 6],
                            [4624625.8, 7],
                            [5622752.337499999, 8],
                            [6400620.6675, 9],
                            [7344282.9525, 10],
                            [8280633.255000001, 11]
                        ]
PROGRESS_BAR_INCREMENT = 0.007662
PROGRESS_BAR_PANEL_OFFSET = 2821000
PROGRESS_BAR_X = 612925.315
PROGRESS_BAR_Y = 3659075.2475
PROGRESS_BAR_SCALE_Y = 0.0508
DOMAIN_NAME_CIRCLE_SCALE = 0.0339
DOMAIN_NAME_CIRCLE_INDICATOR_Y = 1088201.0875

LAST_FRIDAY = datetime.now() + relativedelta(weekday=FR(-1))
LAST_FRIDAY_FORMATTED = '%s/%s/%s' % (LAST_FRIDAY.month, LAST_FRIDAY.day, LAST_FRIDAY.year)
TEMPLATE_FILE = '_ReportsTemplate_v1_Final'
NEW_PRESENTATION_NAME = LAST_FRIDAY_FORMATTED + ' Report'
TITLE_SLIDE_TEXT = 'Domain Reports'

DOMAIN_REPORTS = []
RISK_REPORTS = []
HIGH_RISK_REPORTS = []
MEDIUM_RISK_REPORTS = []
MILESTONE_REPORTS = []
SLIDES = []

# Authentication

STORE = file.Storage(STORAGE_FILE)
CREDS = STORE.get()
HTTP = CREDS.authorize(Http())
SCOPES = (
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/spreadsheets.readonly',
    'https://www.googleapis.com/auth/presentations'
)

if not CREDS or CREDS.invalid:
    FLOW = client.flow_from_clientsecrets(CREDS_FILE, SCOPES)
    CREDS = tools.run_flow(FLOW, STORE)

# APIs

DRIVE_API = discovery.build('drive', 'v3', http=HTTP)
SHEETS_API = discovery.build('sheets', 'v4', http=HTTP)
SLIDES_API = discovery.build('slides', 'v1', http=HTTP)
PRESENTATION_API = SLIDES_API.presentations()

#*------------ Functions ------------*#

def getPresentation():
    return SLIDES_API.presentations().get(presentationId=DECK_ID).execute()

def getSlides():
    return getPresentation().get('slides')

def getSlide(index):
    return PRESENTATION_API.get(presentationId=DECK_ID, fields = 'slides').execute().get('slides')[index]

def batchUpdate():
    return PRESENTATION_API.batchUpdate(presentationId=DECK_ID, body=body).execute()

def getProgBarWidth(percent):
    return percent * PROGRESS_BAR_INCREMENT;

def groupList(lst, N):
    return [lst[n:n+N] for n in range(0, len(lst), N)]

#*------------ Fetch sheet data ------------*#

print('* Fetching sheet data \n')

reports = SHEETS_API.spreadsheets().values().get(range='Sheet1',
            spreadsheetId=DATA_SHEET_ID).execute().get('values')

reports.pop(0)

#*------------ Make new deck from template ------------*#

print('* Making new deck from template')

TEMPLATE = DRIVE_API.files().list(q="name='%s'" % TEMPLATE_FILE).execute()['files'][0]
DATA = {'name': NEW_PRESENTATION_NAME}
DECK = DRIVE_API.files().copy(body=DATA, fileId=TEMPLATE['id']).execute()
DECK_ID = DECK['id']

# Create reports by domain, add risks to proper list and milestones to list

for i, report in enumerate(reports):
    domain = report[12]
    domain_already_in_list = False
    for j, project in enumerate(DOMAIN_REPORTS):
        if domain == project['domain']:
            project['projects'].append(report)
            domain_already_in_list = True

    if domain_already_in_list == False:
        DOMAIN_REPORTS.append({'domain': domain, 'projects': [report]})

    risk = report[14]
    if risk != '' and int(risk) == 2:
        HIGH_RISK_REPORTS.append(report)
    if risk != '' and int(risk) == 1:
        MEDIUM_RISK_REPORTS.append(report)

    milestone = report[8]
    if milestone != '':
        MILESTONE_REPORTS.append(report)

RISK_REPORTS += HIGH_RISK_REPORTS
RISK_REPORTS += MEDIUM_RISK_REPORTS

# Convert arrays into grups of 3 to show 3 per slide
RISK_REPORTS = groupList(RISK_REPORTS, 3)
MILESTONE_REPORTS = groupList(MILESTONE_REPORTS, 3)

# Put three domain projects into each slide

slide_index = -1

for i, domain in enumerate(DOMAIN_REPORTS):
    slide_index += 1
    SLIDES.append([])
    slides_per_domain = math.ceil(len(domain['projects']) / 3)
    print('\t- ' + domain['domain'] + ' has ' + str(len(domain['projects'])) + ' projects and needs ' + str(slides_per_domain) + ' slides')
    for j, project in enumerate(domain['projects']):
        if j != 0 and j%3 == 0:
            slide_index += 1
            SLIDES.append([])

        SLIDES[slide_index].append(project)

#*------------ Duplicate domain report slide based on data ------------*#

print('\n* Making ' + str(len(SLIDES)) + ' duplicates of domain report slide')

for i, slide in enumerate(SLIDES):
    requests = [
        {
            'duplicateObject': {
                'objectId': DOMAIN_REPORT_SLIDE_ID
            }
        }
    ]

    body = {
        'requests': requests
    }

    batch_update = batchUpdate()

#*------------ Delete copied domian report template ------------*#

print('* Deleting domain report template slide')

requests = [
            {
                'deleteObject': {
                    'objectId': DOMAIN_REPORT_SLIDE_ID
                }
            }
        ]

body = {
    'requests': requests
}

batch_update = batchUpdate()

#*------------ Populate Domain report slides ------------*#

print('\n* Populating new domain report slides')

for i, slide in enumerate(SLIDES):
    print('\t- Populating ' + slide[0][12] + ' slide ' + str(i))
    this_slide = getSlide(i)

    #Set empty slide designer array
    designer_list = []

    # If domain_index is marked as 0, it comes through empty. This fixes that.
    domain_index = slide[0][13]
    if domain_index == '':
        domain_index = '0'

    domain_index = int(domain_index)

    requests = [
        # Insert new text to page header
        {
            'insertText': {
                'objectId': this_slide['pageElements'][0]['objectId'],
                'text': slide[0][12]
            }
        },
        # Insert week ending date into report subheader
        {
            'insertText': {
                'objectId': this_slide['pageElements'][1]['objectId'],
                'text': LAST_FRIDAY_FORMATTED,
                'insertionIndex': 29
            }
        },
        # Bold selected domaiin and change color of text
        {
            'updateTextStyle': {
                'objectId': this_slide['pageElements'][SELECTOR_DOT_POSITIONS[domain_index][1]]['objectId'],
                'textRange': {
                    'type': 'ALL'
                },
                'style': {
                    'foregroundColor': {
                        'opaqueColor': {
                            'rgbColor': TEMPLATE_DARK_GRAY
                        }
                    },
                    'bold': True
                },
                'fields': 'foregroundColor, bold'
            }
        },
        # Move circle under domain names
        {
            'updatePageElementTransform': {
                'objectId': this_slide['pageElements'][13]['objectId'],
                'transform': {
                    'scaleX': DOMAIN_NAME_CIRCLE_SCALE,
                    'scaleY': DOMAIN_NAME_CIRCLE_SCALE,
                    'translateX': SELECTOR_DOT_POSITIONS[domain_index][0],
                    'translateY': DOMAIN_NAME_CIRCLE_INDICATOR_Y,
                    'unit': 'EMU'
                },
                'applyMode': 'ABSOLUTE'
            }
        }
    ]

    body = {
        'requests': requests
    }

    batch_update = batchUpdate()

    panel_number = 14
    progress_bar_offset = 0

    for j, project_info in enumerate(slide):
        print('\t\t-- Populating panel ' + str(j))
        this_percentage = int(''.join(filter(str.isdigit, project_info[4])))

        # If risk_index is marked as 0, it comes through empty. This fixes that.
        risk_index = project_info[14]
        if risk_index == '':
            risk_index = '0'
        risk_index = int(risk_index)

        design_lead_name = project_info[15]
        design_lead_image_name = design_lead_name.replace(' ', '_', design_lead_name.count(' ')).lower() + '.png'
        image_file = DRIVE_API.files().list(q="name='%s'" % design_lead_image_name).execute()['files'][0]
        img_url = '%s&access_token=%s' % (
                 DRIVE_API.files().get_media(fileId=image_file['id']).uri, CREDS.access_token)

        requests = []

        if j == 0:
            requests.append(
                # Image for design lead
                ({
                     'createImage': {
                         'url': img_url,
                         'elementProperties': {
                             'pageObjectId': this_slide['objectId'],
                             'size': this_slide['pageElements'][17]['size'],
                             'transform': this_slide['pageElements'][17]['transform']
                         }
                     }
                },
                {
                    'deleteObject': {
                        'objectId': this_slide['pageElements'][17]['objectId']
                    }
                },
                # Insert design lead
                {
                    'insertText': {
                        'objectId': this_slide['pageElements'][18]['objectId'],
                        'text': project_info[15]
                    }
                }
                ))

        requests.append(
            # Insert new text to project header
            ({
                'insertText': {
                    'objectId': this_slide['pageElements'][panel_number]['elementGroup']['children'][2]['objectId'],
                    'text': (project_info[1][:PROJECT_TITLE_CHARACTER_MAX] + '...') if len(project_info[1]) > PROJECT_TITLE_CHARACTER_MAX else project_info[1]
                }
            },
            # Insert new text to project description
            {
                'insertText': {
                    'objectId': this_slide['pageElements'][panel_number]['elementGroup']['children'][3]['objectId'],
                    'text': (project_info[3][:PROJECT_DESCRIPTION_CHARACTER_MAX] + '...') if len(project_info[3]) > PROJECT_DESCRIPTION_CHARACTER_MAX else project_info[3]
                }
            },
            # Insert designer names
            {
                'insertText': {
                    'objectId': this_slide['pageElements'][panel_number]['elementGroup']['children'][4]['objectId'],
                    'text': project_info[2].replace(',', ', ', project_info[2].count(','))
                }
            },
            # Insert percent complete
            {
                'insertText': {
                    'objectId': this_slide['pageElements'][panel_number]['elementGroup']['children'][5]['objectId'],
                    'text': str(this_percentage)
                }
            },
            # Update percentage bar color
            {
                'updateShapeProperties': {
                    'objectId': this_slide['pageElements'][panel_number]['elementGroup']['children'][6]['objectId'],
                    'fields': 'shapeBackgroundFill.solidFill.color',
                    'shapeProperties': {
                        'shapeBackgroundFill': {
                            'solidFill': {
                                'color': {
                                    'rgbColor': PROGRESS_BAR_GRAY
                                }
                            }
                        }
                    }
                }
            },
            # Update progress bar width
            {
                'updatePageElementTransform': {
                    'objectId': this_slide['pageElements'][panel_number]['elementGroup']['children'][6]['objectId'],
                    'transform':{
                        'scaleX': getProgBarWidth(this_percentage),
                        'scaleY': PROGRESS_BAR_SCALE_Y,
                        'translateX': PROGRESS_BAR_X + (PROGRESS_BAR_PANEL_OFFSET * progress_bar_offset),
                        'translateY': PROGRESS_BAR_Y,
                        'unit': 'EMU'
                    },
                    'applyMode': 'ABSOLUTE'
                }
            },
            # Update risk dot color
            {
                'updateShapeProperties': {
                    'objectId': this_slide['pageElements'][panel_number]['elementGroup']['children'][7]['objectId'],
                    'fields': 'shapeBackgroundFill.solidFill.color',
                    'shapeProperties': {
                        'shapeBackgroundFill': {
                            'solidFill': {
                                'color': {
                                    'rgbColor': RISK_COLORS_ARRAY[risk_index]
                                }
                            }
                        }
                    }
                }
            }))

        body = {
            'requests': requests
        }

        batch_update = batchUpdate()

        panel_number += 1
        progress_bar_offset += 1

        # Populate designer_list
        project_designers = project_info[2].split(',')
        for k, designer in enumerate(project_designers):
            # Don't add designer to list if designer is design lead
            if designer != project_info[15]:
                designer_list.append(designer)

        # Remove duplicates from desiner_array
        designer_set = set()
        no_duplicates_designer_list = []
        for designer in designer_list:
            if designer not in designer_set:
                designer_set.add(designer)
                no_duplicates_designer_list.append(designer)

    requests = []

    for remove_panel in range(panel_number, 17):
        remove_req = {
           'deleteObject': {
               'objectId': this_slide['pageElements'][remove_panel]['objectId']
           }
        }
        requests.append(remove_req)

    # Insert designer images and names
    for designer_placeholder in range(DESIGNER_PLACEHOLDER_OFFSET, DESIGNER_PLACEHOLDER_OFFSET + DESIGNER_PLACEHOLDERS):

        if (designer_placeholder - DESIGNER_PLACEHOLDER_OFFSET) < len(no_duplicates_designer_list):
            designer_name = no_duplicates_designer_list[designer_placeholder - DESIGNER_PLACEHOLDER_OFFSET]
            designer_image_name = designer_name.replace(' ', '_', designer_name.count(' ')).lower() + '.png'
            image_file = DRIVE_API.files().list(q="name='%s'" % designer_image_name).execute()['files'][0]
            img_url = '%s&access_token=%s' % (
                     DRIVE_API.files().get_media(fileId=image_file['id']).uri, CREDS.access_token)

            designer_req = (
                {
                     'createImage': {
                         'url': img_url,
                         'elementProperties': {
                             'pageObjectId': this_slide['objectId'],
                             'size': this_slide['pageElements'][designer_placeholder]['size'],
                             'transform': this_slide['pageElements'][designer_placeholder]['transform']
                         }
                     }
                 },
                 {
                     'deleteObject': {
                         'objectId': this_slide['pageElements'][designer_placeholder]['objectId']
                     }
                 },
                 {
                     'insertText': {
                         'objectId': this_slide['pageElements'][designer_placeholder + DESIGNER_PLACEHOLDERS]['objectId'],
                         'text': designer_name
                     }
                 }
            )

        else:
            designer_req = (
                {
                    'deleteObject': {
                        'objectId': this_slide['pageElements'][designer_placeholder]['objectId']
                    }
                },
                {
                    'deleteObject': {
                        'objectId': this_slide['pageElements'][designer_placeholder + DESIGNER_PLACEHOLDERS]['objectId']
                    }
                },)

        requests.append(designer_req)

    if len(requests) != 0:
        body = {
            'requests': requests
        }

        batch_update = batchUpdate()

#*------------ Duplicate risk report slide based on data ------------*#

print('\n* Duplicating risk slides')

for i, risks in enumerate(RISK_REPORTS):
    requests = [
        {
            'duplicateObject': {
                'objectId': RISKS_REPORT_SLIDE_ID
            }
        }
    ]

    body = {
        'requests': requests
    }

    batch_update = batchUpdate()

#*------------ Delete copied risk report template ------------*#
print('* Deleting risk report template slide')

requests = [
            {
                'deleteObject': {
                    'objectId': RISKS_REPORT_SLIDE_ID
                }
            }
        ]

body = {
    'requests': requests
}

batch_update = batchUpdate()

#*------------ Populate Risk report slides ------------*#
risk_report_index = 0

for i in range(len(SLIDES), len(SLIDES) + len(RISK_REPORTS)):
    this_slide = getSlide(i)

    requests = [
        {
            'insertText': {
                'objectId': this_slide['pageElements'][1]['objectId'],
                'text': LAST_FRIDAY_FORMATTED,
                'insertionIndex': 26
            }
        }
    ]

    # Populate Risk panel
    risk_report_panel_index = 0
    for j, risk in enumerate(RISK_REPORTS[risk_report_index]):
        requests.append(
            (
            # Populate risk domain
            {
                'insertText': {
                    'objectId': this_slide['pageElements'][risk_report_panel_index + 2]['elementGroup']['children'][1]['objectId'],
                    'text': risk[12]
                }
            },
            # Populate risk project
            {
                'insertText': {
                    'objectId': this_slide['pageElements'][risk_report_panel_index + 2]['elementGroup']['children'][2]['objectId'],
                    'text': (risk[1][:PROJECT_TITLE_CHARACTER_MAX] + '...') if len(risk[1]) > PROJECT_TITLE_CHARACTER_MAX else risk[1]
                }
            },
            # Populate risk project description
            {
                'insertText': {
                    'objectId': this_slide['pageElements'][risk_report_panel_index + 2]['elementGroup']['children'][3]['objectId'],
                    'text': (risk[3][:PROJECT_DESCRIPTION_CHARACTER_MAX] + '...') if len(risk[3]) > PROJECT_DESCRIPTION_CHARACTER_MAX else risk[3]

                }
            },
            # Populate risk level
            {
                'insertText': {
                    'objectId': this_slide['pageElements'][risk_report_panel_index + 2]['elementGroup']['children'][4]['objectId'],
                    'text': risk[5],
                    'insertionIndex': 12
                }
            },
            # Populate risk description
            {
                'insertText': {
                    'objectId': this_slide['pageElements'][risk_report_panel_index + 2]['elementGroup']['children'][5]['objectId'],
                    'text': (risk[6][:PROJECT_DESCRIPTION_CHARACTER_MAX] + '...') if len(risk[6]) > PROJECT_DESCRIPTION_CHARACTER_MAX else risk[6]
                }
            },
            # Color risk dot
            {
                'updateShapeProperties': {
                    'objectId': this_slide['pageElements'][risk_report_panel_index + 2]['elementGroup']['children'][6]['objectId'],
                    'fields': 'shapeBackgroundFill.solidFill.color',
                    'shapeProperties': {
                        'shapeBackgroundFill': {
                            'solidFill': {
                                'color': {
                                    'rgbColor': RISK_COLORS_ARRAY[int(risk[14])]
                                }
                            }
                        }
                    }
                }
            })
        )
        risk_report_panel_index += 1

    for remove_panel in range(risk_report_panel_index + 2, 5):
        remove_req = {
           'deleteObject': {
               'objectId': this_slide['pageElements'][remove_panel]['objectId']
           }
        }
        requests.append(remove_req)

    body = {
        'requests': requests
    }

    batch_update = batchUpdate()

    risk_report_index += 1

#*------------ Duplicate milestone report slide based on data ------------*#

print('\n* Duplicating milestone slides')

for i, milestones in enumerate(MILESTONE_REPORTS):
    requests = [
        {
            'duplicateObject': {
                'objectId': MILESTONES_REPORT_SLIDE_ID
            }
        }
    ]

    body = {
        'requests': requests
    }

    batch_update = batchUpdate()

#*------------ Delete copied milestone report template ------------*#
print('* Deleting milestone report template slide')

requests = [
            {
                'deleteObject': {
                    'objectId': MILESTONES_REPORT_SLIDE_ID
                }
            }
        ]

body = {
    'requests': requests
}

batch_update = batchUpdate()

#*------------ Populate Milestone report slides ------------*#
milestone_report_index = 0

for i in range((len(SLIDES) + len(RISK_REPORTS)), (len(SLIDES) + len(RISK_REPORTS)) + len(MILESTONE_REPORTS)):
    this_slide = getSlide(i)

    requests = [
        {
            'insertText': {
                'objectId': this_slide['pageElements'][1]['objectId'],
                'text': LAST_FRIDAY_FORMATTED,
                'insertionIndex': 31
            }
        }
    ]

    # Populate milestone panel
    milestone_report_panel_index = 0
    for j, milestone in enumerate(MILESTONE_REPORTS[milestone_report_index]):
        requests.append(
            (
            # Populate milestone domain
            {
                'insertText': {
                    'objectId': this_slide['pageElements'][milestone_report_panel_index + 2]['elementGroup']['children'][1]['objectId'],
                    'text': milestone[12]
                }
            },
            # Populate milestone project
            {
                'insertText': {
                    'objectId': this_slide['pageElements'][milestone_report_panel_index + 2]['elementGroup']['children'][2]['objectId'],
                    'text': (milestone[1][:PROJECT_TITLE_CHARACTER_MAX] + '...') if len(milestone[1]) > PROJECT_TITLE_CHARACTER_MAX else milestone[1]
                }
            },
            # Populate milestone project description
            {
                'insertText': {
                    'objectId': this_slide['pageElements'][milestone_report_panel_index + 2]['elementGroup']['children'][3]['objectId'],
                    'text': (milestone[3][:PROJECT_DESCRIPTION_CHARACTER_MAX] + '...') if len(milestone[3]) > PROJECT_DESCRIPTION_CHARACTER_MAX else milestone[3]

                }
            },
            # Populate milestone description
            {
                'insertText': {
                    'objectId': this_slide['pageElements'][milestone_report_panel_index + 2]['elementGroup']['children'][5]['objectId'],
                    'text': (milestone[8][:PROJECT_DESCRIPTION_CHARACTER_MAX] + '...') if len(milestone[8]) > PROJECT_DESCRIPTION_CHARACTER_MAX else milestone[8]
                }
            })
        )
        milestone_report_panel_index += 1

    for remove_panel in range(milestone_report_panel_index + 2, 5):
        remove_req = {
           'deleteObject': {
               'objectId': this_slide['pageElements'][remove_panel]['objectId']
           }
        }
        requests.append(remove_req)

    body = {
        'requests': requests
    }

    batch_update = batchUpdate()

    milestone_report_index += 1

print('\n* Finished')