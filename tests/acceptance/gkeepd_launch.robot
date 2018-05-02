
*** Settings ***
Library    gkeeprobot.keywords.ServerSetupKeywords
Library    gkeeprobot.keywords.ServerCheckKeywords
Test Setup    Reset Server
Force Tags    gkeepd_launch

*** Test Cases ***

Valid Setup
    [Tags]    happy_path
    Configure Faculty   prof    prof2
    Add File To Server    keeper    files/valid_server.cfg    server.cfg
    Start gkeepd
    Expect Email    to_user=prof    contains=Password
    Expect Email    to_user=prof2   contains=Password
    User Exists    prof
    User Exists    prof2
    User Exists    tester
    Server Running

Faculty Exists
    [Tags]    error
    Add Account On Server    prof
    Configure Faculty    prof
    Add File To Server    keeper    files/valid_server.cfg    server.cfg
    Start gkeepd
    Expect No Email    prof

Duplicate Faculty
    [Tags]    error
    Configure Faculty    prof
    Configure Faculty    prof
    Add File To Server    keeper    files/valid_server.cfg    server.cfg
    Start gkeepd
    Server Not Running
    User Does Not Exist    prof
    Expect No Email    prof

Faculty Named Faculty
    [Tags]    error
    Configure Faculty    faculty
    Add File To Server    keeper    files/valid_server.cfg    server.cfg
    Start gkeepd
    Server Not Running
    User Does Not Exist    faculty
    Expect No Email    faculty

Missing server cfg
    [Tags]    error
    Configure Faculty    prof
    Start gkeepd
    Server Not Running
    User Does Not Exist    prof

Missing faculty csv
    [Tags]    error
    Add File To Server    keeper    files/valid_server.cfg    server.cfg
    Start gkeepd
    Server Not Running

Malformed faculty csv
    [Tags]    error
    Add File To Server    keeper    files/valid_server.cfg    server.cfg
    Add File To Server    keeper    files/malformed_faculty.csv    faculty.csv
    Start gkeepd
    Server Not Running
    User Does Not Exist    prof
    User Does Not Exist    prof2

Malformed server cfg
    [Tags]    error
    Configure Faculty    prof    prof2
    Add File To Server    keeper    files/malformed_server.cfg    server.cfg
    Start gkeepd
    Server Not Running
    User Does Not Exist    prof
    User Does Not Exist    prof2


