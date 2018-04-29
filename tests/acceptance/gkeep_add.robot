
*** Settings ***
Library    gkeeprobot.keywords.ServerSetupKeywords
Library    gkeeprobot.keywords.ServerCheckKeywords
Library    gkeeprobot.keywords.ClientSetupKeywords
Library    gkeeprobot.keywords.ClientCheckKeywords
Resource    resources/setup.robot
Test Setup    Launch Gkeepd With Faculty    washington    adams

*** Test Cases ***

Valid Class
    Setup Faculty Accounts    washington
    Add To Class    faculty=washington    class_name=cs1    student=kermit
    Add To Class    faculty=washington    class_name=cs1    student=gonzo
    Gkeep Add Succeeds    faculty=washington    class_name=cs1
    User Exists    kermit
    User Exists    gonzo
    Expect Email    to_user=kermit    contains=Password
    Expect Email    to_user=gonzo    contains=Password
    Gkeep Query Contains    washington    classes    cs1
    Gkeep Query Contains    washington    students    kermit    gonzo

Missing CSV
    Setup Faculty Accounts    washington
    Gkeep Add Fails    faculty=washington    class_name=cs1

Existing Student
    Setup Faculty Accounts    washington
    Add Account on Server    gonzo
    Add To Class    faculty=washington    class_name=cs1    student=kermit
    Add To Class    faculty=washington    class_name=cs1    student=gonzo
    Gkeep Add Succeeds    faculty=washington    class_name=cs1
    User Exists    kermit
    User Exists    gonzo
    Expect Email    to_user=kermit    contains=Password
    Expect No Email    to_user=gonzo
    Gkeep Query Contains    washington    classes    cs1
    Gkeep Query Contains    washington    students    kermit    gonzo

Call Add Twice
    Setup Faculty Accounts    washington
    Add To Class    faculty=washington    class_name=cs1    student=kermit
    Gkeep Add Succeeds    faculty=washington    class_name=cs1
    Gkeep Add Fails    faculty=washington    class_name=cs1
    Gkeep Query Contains    washington    classes    cs1
    Gkeep Query Contains    washington    students    kermit

Duplicate Student
    Setup Faculty Accounts    washington
    Add To Class    faculty=washington    class_name=cs1    student=kermit
    Add To Class    faculty=washington    class_name=cs1    student=kermit
    Gkeep Add Fails    faculty=washington    class_name=cs1

Malformed CSV
    Setup Faculty Accounts    washington
    Add File To Client    washington    files/malformed_cs1.csv    cs1.csv
    Gkeep Add Fails    faculty=washington    class_name=cs1

Student Named Student
    Setup Faculty Accounts    washington
    Add To Class    faculty=washington    class_name=cs1    student=student
    Gkeep Add Fails    faculty=washington    class_name=cs1

Duplicate Class Name
    Setup Faculty Accounts    washington    adams
    Add To Class    faculty=washington    class_name=cs1    student=kermit
    Gkeep Add Succeeds    faculty=washington    class_name=cs1
    Add To Class    faculty=adams    class_name=cs1    student=gonzo
    Gkeep Add Fails    faculty=adams    class_name=cs1

Empty CSV
    Setup Faculty Accounts    washington
    Make Empty File    washington    cs1.csv
    Gkeep Add Fails    faculty=washington    class_name=cs1