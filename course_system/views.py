from django.http import HttpResponse, FileResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt
from course_app.models import User, Message, Course, Prerequisite, Student, Select, Courseware
from datetime import datetime
from django.db.models import Q
import time
from random import sample
import os
from django.conf import settings


@csrf_exempt
def login(request):
    msg = ''
    if request.method == 'POST':
        inputuserid = request.POST.get('userid')
        inputpassword = request.POST.get('password')
        try:
            if User.objects.filter(userid=inputuserid, password=inputpassword).count() == 0:
                raise RuntimeError
            user = User.objects.filter(userid=inputuserid).values()[
                0]
            request.session['islogin'] = True
            request.session['usertype'] = user['usertype']
            request.session['username'] = user['username']
            request.session['userid'] = inputuserid
            return render(request, 'home.html', {'func': 'myprofile', 'usercollege': user['usercollege']})
        except:
            msg = "用户ID或密码错误，请重新输入！"
    return render(request, 'login.html', {'msg': msg})


@csrf_exempt
def register(request):
    msg = ''
    if request.method == "POST":
        inputuserid = request.POST.get('userid')
        inputpassword = request.POST.get('password')
        inputrecpassword = request.POST.get('recpassword')
        inputname = request.POST.get('name')
        inputcollege = request.POST.get('college')
        inputtype = int(request.POST.get('type'))
        try:
            if len(inputuserid) > 20 or len(inputuserid) == 0 or len(inputpassword) > 20 or len(inputpassword) == 0 or len(inputrecpassword) > 20 or len(inputrecpassword) == 0 or len(inputname) > 20 or len(inputname) == 0 or inputpassword != inputrecpassword or (inputtype != 0 and inputcollege == "教务处") or (inputtype == 0 and inputcollege != "教务处"):
                msg = "信息格式错误，请重新输入！"
                raise RuntimeError
            if User.objects.filter(userid=inputuserid).count() > 0:
                msg = "用户ID已被占用，请重新输入！"
                raise RuntimeError
            user = User(userid=inputuserid, password=inputpassword,
                        username=inputname, usertype=inputtype, usercollege=inputcollege)
            user.save()
            msg = "注册成功，请点击返回按钮进入登录界面！"
        except:
            pass
    return render(request, 'register.html', {'msg': msg})


def addvpre(ida, edge, rudu, v):
    for i in Prerequisite.objects.filter(courseid=ida).values():
        v.add(i['precourseid'])
        if i['precourseid'] not in edge:
            edge[i['precourseid']] = []
        if ida not in rudu:
            rudu[ida] = int(0)
        if ida not in edge[i['precourseid']]:
            edge[i['precourseid']].append(ida)
            rudu[ida] += 1
        if Prerequisite.objects.filter(courseid=i['precourseid']).count():
            addvpre(i['precourseid'], edge, rudu, v)


def addvnext(ida, edge, rudu, v):
    for i in Prerequisite.objects.filter(precourseid=ida).values():
        v.add(i['courseid'])
        if ida not in edge:
            edge[ida] = []
        if i['courseid'] not in rudu:
            rudu[i['courseid']] = int(0)
        if i['courseid'] not in edge[ida]:
            edge[ida].append(i['courseid'])
            rudu[i['courseid']] += 1
        if Prerequisite.objects.filter(precourseid=i['courseid']).count():
            addvnext(i['courseid'], edge, rudu, v)


def topo(ida, idb):
    edge = {}
    rudu = {}
    v = set()
    addvpre(ida, edge, rudu, v)
    addvnext(ida, edge, rudu, v)
    addvpre(idb, edge, rudu, v)
    addvnext(idb, edge, rudu, v)
    if idb not in edge:
        edge[idb] = []
    if ida not in rudu:
        rudu[ida] = int(0)  
    edge[idb].append(ida)
    rudu[ida] += 1
    v.add(ida)
    v.add(idb)
    clist = []
    cnt = int(0)
    for i in v:
        if i not in rudu:
            rudu[i] = int(0)
        if i not in edge:
            edge[i] = []
    for i in rudu:
        if rudu[i] == 0:
            clist.append(i)
    # print('edge:',edge)
    # print('rudu:',rudu)
    # print('v:',v)
    while len(clist) > 0:
        idt = clist[0]
        clist.pop(0)
        cnt += 1
        # print(cnt,idt)
        for i in edge[idt]:
            rudu[i] -= 1
            if rudu[i] == 0:
                clist.append(i)
    if cnt < len(v):
        return False
    else:
        return True


@csrf_exempt
def home(request):
    func = 'myprofile'
    islogin = request.session.get('islogin')
    if not islogin:
        return redirect('/login/')
    userid = request.session.get('userid')
    user = User.objects.filter(userid=userid).values()[0]

    class Msgr:
        def __init__(self, sentid, sentname, messagetime, content):
            self.sentid = sentid
            self.sentname = sentname
            self.messagetime = messagetime
            self.content = content
    messages = Message.objects.filter(receiveid_id=userid).values()
    messagelistr = []
    for message in messages:
        sentid = message['sentid_id']
        sentname = message['sentname']
        messagetime = message['messagetime']
        content = message['content']
        msg = Msgr(sentid, sentname, messagetime, content)
        messagelistr.append(msg)
    messagenumr = len(messagelistr)

    class Msgs:
        def __init__(self, receiveid, reveivename, messagetime, content):
            self.receiveid = receiveid
            self.receivename = receivename
            self.messagetime = messagetime
            self.content = content
    messages = Message.objects.filter(sentid_id=userid).values()
    messagelists = []
    for message in messages:
        receiveid = message['receiveid_id']
        receivename = message['receivename']
        messagetime = message['messagetime']
        content = message['content']
        msg = Msgs(receiveid, receivename, messagetime, content)
        messagelists.append(msg)
    messagenums = len(messagelists)

    if request.method == 'GET':
        logout = request.GET.get('logout')
        if logout == 'True':
            request.session.flush()
            return redirect('/login/')
        messagerefresh = request.GET.get('messagerefresh')
        if messagerefresh == 'True':
            return render(request, 'home.html', {'func': 'message', 'messagenumr': messagenumr, 'messagelistr': messagelistr, 'messagenums': messagenums, 'messagelists': messagelists})
        messagefind = request.GET.get('messagefind')
        if messagefind == 'True':
            messageusername = request.GET.get('messageusername')
            messageusercollege = request.GET.get('messageusercollege')
            messageusertype = int(request.GET.get('messageusertype'))
            if len(messageusername) > 20:
                return render(request, 'home.html', {'func': 'message', 'messagenumr': messagenumr, 'messagelistr': messagelistr, 'ismessagefind': 'False', 'anchor': 'anchor_messagefind'})
            messagefind = User.objects.filter(
                usercollege=messageusercollege, usertype=messageusertype)
            if len(messageusername) > 0:
                messagefind = messagefind.filter(
                    Q(username__contains=messageusername))
            messagefind = messagefind.values()
            messagefindlist = []

            class Msgfind:
                def __init__(self, userid, username, usertype, usercollege):
                    self.userid = userid
                    self.username = username
                    self.usertype = usertype
                    self.usercollege = usercollege
            for msgfind in messagefind:
                userid = msgfind['userid']
                username = msgfind['username']
                msgfindtype = msgfind['usertype']
                if msgfindtype == 0:
                    usertype = '系统管理员'
                elif msgfindtype == 1:
                    usertype = '学院管理员'
                elif msgfindtype == 2:
                    usertype = '教师'
                elif msgfindtype == 3:
                    usertype = '学生'
                usercollege = msgfind['usercollege']
                msg = Msgfind(userid, username, usertype, usercollege)
                messagefindlist.append(msg)
            messagefindnum = len(messagefindlist)
            return render(request, 'home.html', {'func': 'message', 'messagenumr': messagenumr, 'messagelistr': messagelistr, 'messagenums': messagenums, 'messagelists': messagelists, 'ismessagefind': 'True', 'messagefindnum': messagefindnum, 'messagefindlist': messagefindlist, 'anchor': 'anchor_messagefind'})
        messagesent = request.GET.get('messagesent')
        if messagesent == 'True':
            sentuserid = request.GET.get('sentuserid')
            sentcontent = request.GET.get('sentcontent')
            if len(sentuserid) > 20 or len(sentuserid) == 0 or len(sentcontent) > 100 or len(sentcontent) == 0 or User.objects.filter(userid=sentuserid).count() == 0:
                return render(request, 'home.html', {'func': 'message', 'messagenumr': messagenumr, 'messagelistr': messagelistr, 'messagenums': messagenums, 'messagelists': messagelists, 'ismessagesent': 'False', 'anchor': 'anchor_messagesent'})
            receiveuser = User.objects.filter(userid=sentuserid).values()[0]
            msg = Message(sentid_id=userid, sentname=user['username'], receiveid_id=sentuserid,
                          receivename=receiveuser['username'], messagetime=time.strftime(
                              "%Y-%m-%d %H:%M:%S", time.localtime()),
                          content=sentcontent)
            msg.save()
            return render(request, 'home.html', {'func': 'message', 'messagenumr': messagenumr, 'messagelistr': messagelistr, 'messagenums': messagenums, 'messagelists': messagelists, 'ismessagesent': 'True', 'anchor': 'anchor_messagesent'})
        newstu = request.GET.get('newstu')
        if newstu == 'True':
            newxsid = request.GET.get('newxsid')
            newxspassword = request.GET.get('newxspassword')
            newxsrecpassword = request.GET.get('newxsrecpassword')
            newxsname = request.GET.get('newxsname')
            if request.session.get('usertype') == 0:
                newxscollege = request.GET.get('newxscollege')
            else:
                newxscollege = user['usercollege']
            if len(newxsid) > 20 or len(newxsid) == 0 or len(newxspassword) > 20 or len(newxspassword) == 0 or len(newxsrecpassword) > 20 or len(newxsrecpassword) == 0 or len(newxsname) > 20 or len(newxsname) == 0 or newxspassword != newxsrecpassword:
                return render(request, 'home.html', {'func': 'xsmanage', 'usercollege': user['usercollege'], 'isnewstu': 'False', 'newstumsg': '信息格式错误，请重新输入！'})
            if User.objects.filter(userid=newxsid).count() > 0:
                return render(request, 'home.html', {'func': 'xsmanage', 'usercollege': user['usercollege'], 'isnewstu': 'False', 'newstumsg': '用户名已被占用，请重新输入！'})
            newxsuser = User(userid=newxsid, password=newxspassword,
                             username=newxsname, usertype=3, usercollege=newxscollege)
            newxsuser.save()
            return render(request, 'home.html', {'func': 'xsmanage', 'usercollege': user['usercollege'], 'isnewstu': 'True', 'newstumsg': '成功增加学生用户！'})
        delstu = request.GET.get('delstu')
        if delstu == 'True':
            delxsid = request.GET.get('delxsid')
            if User.objects.filter(userid=delxsid).count() == 0:
                return render(request, 'home.html', {'func': 'xsmanage', 'usercollege': user['usercollege'], 'isdelstu': 'False', 'delstumsg': '用户不存在，请重新输入！', 'anchor': 'anchor_delstu'})
            delxsuser = User.objects.filter(userid=delxsid).values()[0]
            if request.session.get('usertype') == 1 and delxsuser['usercollege'] != user['usercollege']:
                return render(request, 'home.html', {'func': 'xsmanage', 'usercollege': user['usercollege'], 'isdelstu': 'False', 'delstumsg': '非本学院用户，权限不足，请重新输入！', 'anchor': 'anchor_delstu'})
            if delxsuser['usertype'] != 3:
                return render(request, 'home.html', {'func': 'xsmanage', 'usercollege': user['usercollege'], 'isdelstu': 'False', 'delstumsg': '用户非学生，请重新输入！', 'anchor': 'anchor_delstu'})
            Message.objects.filter(Q(receiveid_id=delxsid)
                                   | Q(sentid_id=delxsid)).delete()
            Select.objects.filter(studentid=delxsid).delete()
            altlist = []
            delstu = Student.objects.filter(studentid=delxsid).values()
            for du in delstu:
                courseid = du['courseid']
                score = du['score']
                cs = Course.objects.filter(courseid=courseid).values()[0]
                studentnum = cs['studentnum'] - 1
                Course.objects.filter(courseid=courseid).update(
                    studentnum=studentnum)
                if score is not None:
                    altlist.append(courseid)
                    if score > 85:
                        Course.objects.filter(courseid=courseid).update(
                            outstandingnum=cs['outstandingnum']-1)
                    elif score > 59:
                        Course.objects.filter(courseid=courseid).update(
                            goodnum=cs['goodnum']-1)
                    else:
                        Course.objects.filter(courseid=courseid).update(
                            failnum=cs['failnum']-1)
            Student.objects.filter(studentid=delxsid).delete()
            for altc in altlist:
                stu = Student.objects.filter(courseid=altc).values()
                amt = int(0)
                peo = int(0)
                for su in stu:
                    if su['score'] is not None:
                        peo += 1
                        if su['score'] > 59:
                            amt += 1
                Course.objects.filter(
                    courseid=altc).update(passratio=amt/peo)
            User.objects.filter(userid=delxsid).delete()
            return render(request, 'home.html', {'func': 'xsmanage', 'usercollege': user['usercollege'], 'isdelstu': 'True', 'delstumsg': '成功删除学生用户！', 'anchor': 'anchor_delstu'})
        altstu = request.GET.get('altstu')
        if altstu == 'True':
            altxsid = request.GET.get('altxsid')
            if User.objects.filter(userid=altxsid).count() == 0:
                return render(request, 'home.html', {'func': 'xsmanage', 'usercollege': user['usercollege'], 'isaltstu': 'False', 'altstumsg': '用户不存在，请重新输入！', 'anchor': 'anchor_altstu'})
            altxsuser = User.objects.filter(userid=altxsid).values()[0]
            if request.session.get('usertype') == 1 and altxsuser['usercollege'] != user['usercollege']:
                return render(request, 'home.html', {'func': 'xsmanage', 'usercollege': user['usercollege'], 'isaltstu': 'False', 'altstumsg': '非本学院用户，权限不足，请重新输入！', 'anchor': 'anchor_altstu'})
            if altxsuser['usertype'] != 3:
                return render(request, 'home.html', {'func': 'xsmanage', 'usercollege': user['usercollege'], 'isaltstu': 'False', 'altstumsg': '用户非学生，请重新输入！', 'anchor': 'anchor_altstu'})
            altxspassword = request.GET.get('altxspassword')
            altxsrecpassword = request.GET.get('altxsrecpassword')
            altxsname = request.GET.get('altxsname')
            if altxspassword != altxsrecpassword or len(altxsname) > 20:
                return render(request, 'home.html', {'func': 'xsmanage', 'usercollege': user['usercollege'], 'isaltstu': 'False', 'altstumsg': '信息格式错误，请重新输入！', 'anchor': 'anchor_altstu'})
            altxsuser = User.objects.get(userid=altxsid)
            if request.session.get('usertype') == 0:
                altxscollege = request.GET.get('altxscollege')
                if altxscollege != '不修改':
                    altxsuser.usercollege = altxscollege
            if len(altxspassword) > 0:
                altxsuser.password = altxspassword
            if len(altxsname) > 0:
                Message.objects.filter(
                    sentid_id=altxsid).update(sentname=altxsname)
                Message.objects.filter(
                    receiveid_id=altxsid).update(receivename=altxsname)
                altxsuser.username = altxsname
            altxsuser.save()
            return render(request, 'home.html', {'func': 'xsmanage', 'usercollege': user['usercollege'], 'isaltstu': 'True', 'altstumsg': '成功修改学生用户！', 'anchor': 'anchor_altstu'})
        newjs = request.GET.get('newjs')
        if newjs == 'True':
            newjsid = request.GET.get('newjsid')
            newjspassword = request.GET.get('newjspassword')
            newjsrecpassword = request.GET.get('newjsrecpassword')
            newjsname = request.GET.get('newjsname')
            if request.session.get('usertype') == 0:
                newjscollege = request.GET.get('newjscollege')
            else:
                newjscollege = user['usercollege']
            if len(newjsid) > 20 or len(newjsid) == 0 or len(newjspassword) > 20 or len(newjspassword) == 0 or len(newjsrecpassword) > 20 or len(newjsrecpassword) == 0 or len(newjsname) > 20 or len(newjsname) == 0 or newjspassword != newjsrecpassword:
                return render(request, 'home.html', {'func': 'jsmanage', 'usercollege': user['usercollege'], 'isnewjs': 'False', 'newjsmsg': '信息格式错误，请重新输入！'})
            if User.objects.filter(userid=newjsid).count() > 0:
                return render(request, 'home.html', {'func': 'jsmanage', 'usercollege': user['usercollege'], 'isnewjs': 'False', 'newjsmsg': '用户名已被占用，请重新输入！'})
            newjsuser = User(userid=newjsid, password=newjspassword,
                             username=newjsname, usertype=2, usercollege=newjscollege)
            newjsuser.save()
            return render(request, 'home.html', {'func': 'jsmanage', 'usercollege': user['usercollege'], 'isnewjs': 'True', 'newjsmsg': '成功增加教师用户！'})
        deljs = request.GET.get('deljs')
        if deljs == 'True':
            deljsid = request.GET.get('deljsid')
            if User.objects.filter(userid=deljsid).count() == 0:
                return render(request, 'home.html', {'func': 'jsmanage', 'usercollege': user['usercollege'], 'isdeljs': 'False', 'deljsmsg': '用户不存在，请重新输入！', 'anchor': 'anchor_deljs'})
            deljsuser = User.objects.filter(userid=deljsid).values()[0]
            if request.session.get('usertype') == 1 and deljsuser['usercollege'] != user['usercollege']:
                return render(request, 'home.html', {'func': 'jsmanage', 'usercollege': user['usercollege'], 'isdeljs': 'False', 'deljsmsg': '非本学院用户，权限不足，请重新输入！', 'anchor': 'anchor_deljs'})
            if deljsuser['usertype'] != 2:
                return render(request, 'home.html', {'func': 'jsmanage', 'usercollege': user['usercollege'], 'isdeljs': 'False', 'deljsmsg': '用户非教师，请重新输入！', 'anchor': 'anchor_deljs'})
            for cs in Course.objects.filter(teacherid=deljsid).values():
                csid = cs['courseid']
                Prerequisite.objects.filter(
                    Q(courseid=csid) | Q(precourseid=csid)).delete()
                Student.objects.filter(courseid=csid).delete()
                Select.objects.filter(courseid=csid).delete()
            Course.objects.filter(teacherid=deljsid).delete()
            Message.objects.filter(Q(receiveid_id=deljsid)
                                   | Q(sentid_id=deljsid)).delete()
            User.objects.filter(userid=deljsid).delete()
            return render(request, 'home.html', {'func': 'jsmanage', 'usercollege': user['usercollege'], 'isdeljs': 'True', 'deljsmsg': '成功删除教师用户！', 'anchor': 'anchor_deljs'})
        altjs = request.GET.get('altjs')
        if altjs == 'True':
            altjsid = request.GET.get('altjsid')
            if User.objects.filter(userid=altjsid).count() == 0:
                return render(request, 'home.html', {'func': 'jsmanage', 'usercollege': user['usercollege'], 'isaltjs': 'False', 'altjsmsg': '用户不存在，请重新输入！', 'anchor': 'anchor_altjs'})
            altjsuser = User.objects.filter(userid=altjsid).values()[0]
            if request.session.get('usertype') == 1 and altjsuser['usercollege'] != user['usercollege']:
                return render(request, 'home.html', {'func': 'jsmanage', 'usercollege': user['usercollege'], 'isaltjs': 'False', 'altjsmsg': '非本学院用户，权限不足，请重新输入！', 'anchor': 'anchor_altjs'})
            if altjsuser['usertype'] != 2:
                return render(request, 'home.html', {'func': 'jsmanage', 'usercollege': user['usercollege'], 'isaltjs': 'False', 'altjsmsg': '用户非教师，请重新输入！', 'anchor': 'anchor_altjs'})
            altjspassword = request.GET.get('altjspassword')
            altjsrecpassword = request.GET.get('altjsrecpassword')
            altjsname = request.GET.get('altjsname')
            if altjspassword != altjsrecpassword or len(altjsname) > 20:
                return render(request, 'home.html', {'func': 'jsmanage', 'usercollege': user['usercollege'], 'isaltjs': 'False', 'altjsmsg': '信息格式错误，请重新输入！', 'anchor': 'anchor_altjs'})
            altjsuser = User.objects.get(userid=altjsid)
            if request.session.get('usertype') == 0:
                altjscollege = request.GET.get('altjscollege')
                if altjscollege != '不修改':
                    altjsuser.usercollege = altjscollege
            if len(altjspassword) > 0:
                altjsuser.password = altjspassword
            if len(altjsname) > 0:
                Course.objects.filter(
                    teacherid=altjsid).update(teachername=altjsname)
                Message.objects.filter(
                    sentid_id=altjsid).update(sentname=altjsname)
                Message.objects.filter(
                    receiveid_id=altjsid).update(receivename=altjsname)
                altjsuser.username = altjsname
            altjsuser.save()
            return render(request, 'home.html', {'func': 'jsmanage', 'usercollege': user['usercollege'], 'isaltjs': 'True', 'altjsmsg': '成功修改教师用户！', 'anchor': 'anchor_altjs'})
        fdcourse = request.GET.get('fdcourse')
        if fdcourse == 'True':
            findcoursename = request.GET.get('findcoursename')
            findcoursejsname = request.GET.get('findcoursejsname')
            findcoursecollege = request.GET.get('findcoursecollege')
            findcoursecq = request.GET.get('findcoursecq')
            if len(findcoursename) > 20 or len(findcoursejsname) > 20:
                return render(request, 'home.html', {'func': 'findcourse', 'isfdcourse': 'False'})
            findcourse = Course.objects.filter(
                coursecollege=findcoursecollege, isdrawlots=(findcoursecq == "1"))
            if len(findcoursename) > 0:
                findcourse.filter(Q(coursename__contains=findcoursename))
            if len(findcoursejsname) > 0:
                findcourse.filter(Q(teachername__contains=findcoursejsname))
            findcourse = findcourse.values()
            fdcourselist = []

            class Csfind:
                def __init__(self, courseid, coursename, teachername, coursecollege, isdrawlots, maxnum, introduce, precourse):
                    self.courseid = courseid
                    self.coursename = coursename
                    self.teachername = teachername
                    self.coursecollege = coursecollege
                    self.isdrawlots = isdrawlots
                    self.maxnum = maxnum
                    self.introduce = introduce
                    self.precourse = precourse
            for fdcs in findcourse:
                courseid = fdcs['courseid']
                coursename = fdcs['coursename']
                teachername = fdcs['teachername']
                coursecollege = fdcs['coursecollege']
                if fdcs['isdrawlots'] == True:
                    isdrawlots = '已抽签'
                else:
                    isdrawlots = '未抽签'
                maxnum = fdcs['maxnum']
                introduce = fdcs['introduce']
                precourse = ''
                prec = Prerequisite.objects.filter(
                    courseid=courseid).values()
                for pc in prec:
                    pcid = pc['precourseid']
                    pcs = Course.objects.filter(courseid=pcid).values()[0]
                    pcname = pcs['coursename']
                    precourse += pcname + '(' + pcid + ') '
                if len(precourse) == 0:
                    precourse = '无'
                csf = Csfind(courseid, coursename, teachername,
                             coursecollege, isdrawlots, maxnum, introduce, precourse)
                fdcourselist.append(csf)
            fdcoursenum = len(fdcourselist)
            return render(request, 'home.html', {'func': 'findcourse', 'isfdcourse': 'True', 'fdcoursenum': fdcoursenum, 'fdcourselist': fdcourselist})
        kcmgfd = request.GET.get('kcmgfd')
        if kcmgfd == 'True':
            kcmgfdid = request.GET.get('kcmgfdid')
            if len(kcmgfdid) == 0 or len(kcmgfdid) > 20 or Course.objects.filter(courseid=kcmgfdid).count() == 0:
                return render(request, 'home.html', {'func': 'kcmanage', 'usercollege': user['usercollege'], 'iskcmgfd': 'False'})
            csfd = Course.objects.filter(courseid=kcmgfdid).values()[0]
            if user['usertype'] == 2 and csfd['teacherid'] != userid or user['usertype'] == 1 and csfd['coursecollege'] != user['usercollege']:
                return render(request, 'home.html', {'func': 'kcmanage', 'usercollege': user['usercollege'], 'iskcmgfd': 'Fail'})
            studentnum = csfd['studentnum']
            if studentnum == 0:
                return render(request, 'home.html', {'func': 'kcmanage', 'usercollege': user['usercollege'], 'iskcmgfd': 'True', 'kcmgfdnum': 0})
            passratio = csfd['passratio']
            if passratio is None:
                passratio = '暂无'
            failnum = csfd['failnum']
            if failnum is None:
                failnum = '暂无'
            goodnum = csfd['goodnum']
            if goodnum is None:
                goodnum = '暂无'
            outstandingnum = csfd['outstandingnum']
            if outstandingnum is None:
                outstandingnum = '暂无'
            stufd = Student.objects.filter(courseid=kcmgfdid).values()
            kcmgfdlist = []

            class Scfd:
                def __init__(self, courseid, coursename, studentid, studentname, score):
                    self.courseid = courseid
                    self.coursename = coursename
                    self.studentid = studentid
                    self.studentname = studentname
                    self.score = score
            for sd in stufd:
                courseid = sd['courseid']
                coursename = Course.objects.filter(courseid=courseid).values()[
                    0]['coursename']
                studentid = sd['studentid']
                studentname = User.objects.filter(
                    userid=studentid).values()[0]['username']
                score = sd['score']
                if score is None:
                    score = "暂无"
                sd = Scfd(courseid, coursename, studentid, studentname, score)
                kcmgfdlist.append(sd)
            return render(request, 'home.html', {'func': 'kcmanage', 'usercollege': user['usercollege'], 'iskcmgfd': 'True', 'kcmgfdnum': studentnum, 'kcmgfdlist': kcmgfdlist, 'passratio': passratio, 'failnum': failnum, 'goodnum': goodnum, 'outstandingnum': outstandingnum})
        kcmgnew = request.GET.get('kcmgnew')
        if kcmgnew == 'True':
            kcmgnewid = request.GET.get('kcmgnewid')
            kcmgnewname = request.GET.get('kcmgnewname')
            kcmgnewjsid = request.GET.get('kcmgnewjsid')
            if user['usertype'] == 2:
                kcmgnewjsid = userid
            kcmgnewmaxnum = request.GET.get('kcmgnewmaxnum')
            kcmgnewct = request.GET.get('kcmgnewct')
            if len(kcmgnewid) > 20 or len(kcmgnewname) > 20 or len(kcmgnewjsid) > 20 or len(kcmgnewmaxnum) > 3 or len(kcmgnewct) > 100 or len(kcmgnewid) == 0 or len(kcmgnewname) == 0 or len(kcmgnewjsid) == 0 or len(kcmgnewmaxnum) == 0 or len(kcmgnewct) == 0 or kcmgnewmaxnum.isdigit() == False:
                return render(request, 'home.html', {'func': 'kcmanage', 'usercollege': user['usercollege'], 'iskcmgnew': 'False', 'kcmgnewmsg': '信息格式错误，请重新输入！', 'anchor': 'anchor_kcmgnew'})
            if Course.objects.filter(courseid=kcmgnewid).count() > 0:
                return render(request, 'home.html', {'func': 'kcmanage', 'usercollege': user['usercollege'], 'iskcmgnew': 'False', 'kcmgnewmsg': '课程ID已被占用，请重新输入！', 'anchor': 'anchor_kcmgnew'})
            if User.objects.filter(userid=kcmgnewjsid).count() == 0 or User.objects.filter(userid=kcmgnewjsid).values()[0]['usertype'] != 2:
                return render(request, 'home.html', {'func': 'kcmanage', 'usercollege': user['usercollege'], 'iskcmgnew': 'False', 'kcmgnewmsg': '教师不存在，请重新输入！', 'anchor': 'anchor_kcmgnew'})
            if user['usertype'] == 1 and User.objects.filter(userid=kcmgnewjsid).values()[0]['usercollege'] != user['usercollege']:
                return render(request, 'home.html', {'func': 'kcmanage', 'usercollege': user['usercollege'], 'iskcmgnew': 'False', 'kcmgnewmsg': '非本学院教师，权限不足，请重新输入！', 'anchor': 'anchor_kcmgnew'})
            cs = Course(courseid=kcmgnewid, coursename=kcmgnewname, teacherid=kcmgnewjsid,
                        teachername=User.objects.filter(userid=kcmgnewjsid).values()[0]['username'], coursecollege=User.objects.filter(userid=kcmgnewjsid).values()[0]['usercollege'], maxnum=int(kcmgnewmaxnum), introduce=kcmgnewct, isdrawlots=False)
            cs.save()
            return render(request, 'home.html', {'func': 'kcmanage', 'usercollege': user['usercollege'], 'iskcmgnew': 'True', 'kcmgnewmsg': '成功增加课程！', 'anchor': 'anchor_kcmgnew'})
        kcmgdel = request.GET.get('kcmgdel')
        if kcmgdel == 'True':
            kcmgdelid = request.GET.get('kcmgdelid')
            if Course.objects.filter(courseid=kcmgdelid).count() == 0:
                return render(request, 'home.html', {'func': 'kcmanage', 'usercollege': user['usercollege'], 'iskcmgdel': 'False', 'kcmgdelmsg': '课程不存在，请重新输入！', 'anchor': 'anchor_kcmgdel'})
            if request.session.get('usertype') == 1 and Course.objects.filter(courseid=kcmgdelid).values()[0]['coursecollege'] != user['usercollege'] or request.session.get('usertype') == 2 and Course.objects.filter(courseid=kcmgdelid).values()[0]['teacherid'] != userid:
                return render(request, 'home.html', {'func': 'kcmanage', 'usercollege': user['usercollege'], 'iskcmgdel': 'False', 'kcmgdelmsg': '非管理范围内课程，权限不足，请重新输入！', 'anchor': 'anchor_kcmgdel'})
            Prerequisite.objects.filter(
                Q(courseid=kcmgdelid) | Q(precourseid=kcmgdelid)).delete()
            Student.objects.filter(courseid=kcmgdelid).delete()
            Select.objects.filter(courseid=kcmgdelid).delete()
            Course.objects.filter(courseid=kcmgdelid).delete()
            return render(request, 'home.html', {'func': 'kcmanage', 'usercollege': user['usercollege'], 'iskcmgdel': 'True', 'kcmgdelmsg': '成功删除课程！', 'anchor': 'anchor_kcmgdel'})
        kcmgalt = request.GET.get('kcmgalt')
        if kcmgalt == 'True':
            kcmgaltid = request.GET.get('kcmgaltid')
            kcmgaltjsid = request.GET.get('kcmgaltjsid')
            if user['usertype'] == 2:
                kcmgaltjsid = userid
            kcmgaltname = request.GET.get('kcmgaltname')
            kcmgaltmaxnum = request.GET.get('kcmgaltmaxnum')
            kcmgaltct = request.GET.get('kcmgaltct')
            if len(kcmgaltid) > 20 or len(kcmgaltid) == 0 or len(kcmgaltjsid) > 20 or len(kcmgaltname) > 20 or len(kcmgaltmaxnum) > 3 or (len(kcmgaltmaxnum) > 0 and kcmgaltmaxnum.isdigit() == False) or len(kcmgaltct) > 100:
                return render(request, 'home.html', {'func': 'kcmanage', 'usercollege': user['usercollege'], 'iskcmgalt': 'False', 'kcmgaltmsg': '信息格式错误，请重新输入！', 'anchor': 'anchor_kcmgalt'})
            if Course.objects.filter(courseid=kcmgaltid).count() == 0:
                return render(request, 'home.html', {'func': 'kcmanage', 'usercollege': user['usercollege'], 'iskcmgalt': 'False', 'kcmgaltmsg': '课程不存在，请重新输入！', 'anchor': 'anchor_kcmgalt'})
            altkc = Course.objects.filter(courseid=kcmgaltid).values()[0]
            if request.session.get('usertype') == 1 and altkc['coursecollege'] != user['usercollege'] or request.session.get('usertype') == 2 and altkc['teacherid'] != userid:
                return render(request, 'home.html', {'func': 'kcmanage', 'usercollege': user['usercollege'], 'iskcmgalt': 'False', 'kcmgaltmsg': '非管理范围内课程，权限不足，请重新输入！', 'anchor': 'anchor_kcmgalt'})
            if len(kcmgaltjsid) > 0:
                if User.objects.filter(userid=kcmgaltjsid).count() == 0 or User.objects.filter(userid=kcmgaltjsid).values()[0]['usertype'] != 2:
                    return render(request, 'home.html', {'func': 'kcmanage', 'usercollege': user['usercollege'], 'iskcmgalt': 'False', 'kcmgaltmsg': '教师不存在，请重新输入！', 'anchor': 'anchor_kcmgalt'})
                if request.session.get('usertype') == 1 and User.objects.filter(userid=kcmgaltjsid).values()[0]['usertype'] == 2 and User.objects.filter(userid=kcmgaltjsid).values()[0]['usercollege'] != user['usercollege']:
                    return render(request, 'home.html', {'func': 'kcmanage', 'usercollege': user['usercollege'], 'iskcmgalt': 'False', 'kcmgaltmsg': '非本学院教师，权限不足，请重新输入！', 'anchor': 'anchor_kcmgalt'})
            if len(kcmgaltmaxnum) > 0 and altkc['isdrawlots'] == True:
                return render(request, 'home.html', {'func': 'kcmanage', 'usercollege': user['usercollege'], 'iskcmgalt': 'False', 'kcmgaltmsg': '课程已经抽签，无法修改课堂容量，请重新输入！', 'anchor': 'anchor_kcmgalt'})
            if len(kcmgaltname) > 0:
                Course.objects.filter(courseid=kcmgaltid).update(
                    coursename=kcmgaltname)
            if len(kcmgaltjsid) > 0:
                Course.objects.filter(courseid=kcmgaltid).update(
                    teacherid=kcmgaltjsid)
                Course.objects.filter(courseid=kcmgaltid).update(
                    teachername=User.objects.filter(userid=kcmgaltjsid).values()[0]['username'])
                Course.objects.filter(courseid=kcmgaltid).update(
                    coursecollege=User.objects.filter(userid=kcmgaltjsid).values()[0]['usercollege'])
            if len(kcmgaltmaxnum) > 0:
                Course.objects.filter(courseid=kcmgaltid).update(
                    maxnum=int(kcmgaltmaxnum))
            if len(kcmgaltct) > 0:
                Course.objects.filter(courseid=kcmgaltid).update(
                    introduce=kcmgaltct)
            return render(request, 'home.html', {'func': 'kcmanage', 'usercollege': user['usercollege'], 'iskcmgalt': 'True', 'kcmgaltmsg': '成功修改课程！', 'anchor': 'anchor_kcmgalt'})
        kcmgxx = request.GET.get('kcmgxx')
        if kcmgxx == 'True':
            kcmgxxid = request.GET.get('kcmgxxid')
            kcmgxxpid = request.GET.get('kcmgxxpid')
            if len(kcmgxxpid) > 20 or len(kcmgxxpid) == 0 or kcmgxxpid == kcmgxxid or len(kcmgxxid) > 20 or len(kcmgxxid) == 0:
                return render(request, 'home.html', {'func': 'kcmanage', 'usercollege': user['usercollege'], 'iskcmgxx': 'False', 'kcmgxxmsg': '信息格式错误，请重新输入！', 'anchor': 'anchor_kcmgxx'})
            if Course.objects.filter(courseid=kcmgxxid).count() == 0 or Course.objects.filter(courseid=kcmgxxpid).count() == 0:
                return render(request, 'home.html', {'func': 'kcmanage', 'usercollege': user['usercollege'], 'iskcmgxx': 'False', 'kcmgxxmsg': '课程不存在，请重新输入！', 'anchor': 'anchor_kcmgxx'})
            xxcs = Course.objects.filter(courseid=kcmgxxid).values()[0]
            if request.session.get('usertype') == 1 and xxcs['coursecollege'] != user['usercollege'] or request.session.get('usertype') == 2 and xxcs['teacherid'] != userid:
                return render(request, 'home.html', {'func': 'kcmanage', 'usercollege': user['usercollege'], 'iskcmgxx': 'False', 'kcmgxxmsg': '非管理范围内课程，权限不足，请重新输入！', 'anchor': 'anchor_kcmgxx'})
            if Prerequisite.objects.filter(courseid=kcmgxxid, precourseid=kcmgxxpid).count() > 0:
                return render(request, 'home.html', {'func': 'kcmanage', 'usercollege': user['usercollege'], 'iskcmgxx': 'False', 'kcmgxxmsg': '请勿重复设置先修课程！', 'anchor': 'anchor_kcmgxx'})
            if Course.objects.filter(courseid=kcmgxxid).values()[0]['isdrawlots'] == True or Course.objects.filter(courseid=kcmgxxpid).values()[0]['isdrawlots'] == True or (Course.objects.filter(courseid=kcmgxxid).values()[0]['isdrawlots'] == False and Select.objects.filter(courseid=kcmgxxid).count()):
                return render(request, 'home.html', {'func': 'kcmanage', 'usercollege': user['usercollege'], 'iskcmgxx': 'False', 'kcmgxxmsg': '已经开始选课，无法设置先修课程！', 'anchor': 'anchor_kcmgxx'})
            if Prerequisite.objects.filter(courseid=kcmgxxpid, precourseid=kcmgxxid).count() > 0 or topo(kcmgxxid, kcmgxxpid) == False:
                return render(request, 'home.html', {'func': 'kcmanage', 'usercollege': user['usercollege'], 'iskcmgxx': 'False', 'kcmgxxmsg': '产生循环依赖，请重新输入！', 'anchor': 'anchor_kcmgxx'})
            pt = Prerequisite(courseid=kcmgxxid, precourseid=kcmgxxpid)
            pt.save()
            return render(request, 'home.html', {'func': 'kcmanage', 'usercollege': user['usercollege'], 'iskcmgxx': 'True', 'kcmgxxmsg': '成功设置先修课程！', 'anchor': 'anchor_kcmgxx'})
        kcmgxxdel = request.GET.get('kcmgxxdel')
        if kcmgxxdel == 'True':
            kcmgxxdelid = request.GET.get('kcmgxxdelid')
            kcmgxxdelpid = request.GET.get('kcmgxxdelpid')
            if len(kcmgxxdelpid) > 20 or len(kcmgxxdelpid) == 0 or kcmgxxdelpid == kcmgxxdelid or len(kcmgxxdelid) > 20 or len(kcmgxxdelid) == 0:
                return render(request, 'home.html', {'func': 'kcmanage', 'usercollege': user['usercollege'], 'iskcmgxxdel': 'False', 'kcmgxxdelmsg': '信息格式错误，请重新输入！', 'anchor': 'anchor_kcmgxxdel'})
            if Course.objects.filter(courseid=kcmgxxdelid).count() == 0:
                return render(request, 'home.html', {'func': 'kcmanage', 'usercollege': user['usercollege'], 'iskcmgxxdel': 'False', 'kcmgxxdelmsg': '课程不存在，请重新输入！', 'anchor': 'anchor_kcmgxxdel'})
            xxcs = Course.objects.filter(courseid=kcmgxxdelid).values()[0]
            if request.session.get('usertype') == 1 and xxcs['coursecollege'] != user['usercollege'] or request.session.get('usertype') == 2 and xxcs['teacherid'] != userid:
                return render(request, 'home.html', {'func': 'kcmanage', 'usercollege': user['usercollege'], 'iskcmgxxdel': 'False', 'kcmgxxdelmsg': '非管理范围内课程，权限不足，请重新输入！', 'anchor': 'anchor_kcmgxxdel'})
            if Prerequisite.objects.filter(courseid=kcmgxxdelid, precourseid=kcmgxxdelpid).count() == 0:
                return render(request, 'home.html', {'func': 'kcmanage', 'usercollege': user['usercollege'], 'iskcmgxxdel': 'False', 'kcmgxxdelmsg': '先修课程记录不存在，请重新输入！', 'anchor': 'anchor_kcmgxxdel'})
            Prerequisite.objects.filter(
                courseid=kcmgxxdelid, precourseid=kcmgxxdelpid).delete()
            return render(request, 'home.html', {'func': 'kcmanage', 'usercollege': user['usercollege'], 'iskcmgxxdel': 'True', 'kcmgxxdelmsg': '成功删除先修课程！', 'anchor': 'anchor_kcmgxxdel'})
        kcmgxxalt = request.GET.get('kcmgxxalt')
        if kcmgxxalt == 'True':
            kcmgxxaltid = request.GET.get('kcmgxxaltid')
            kcmgxxaltpid = request.GET.get('kcmgxxaltpid')
            kcmgxxaltnid = request.GET.get('kcmgxxaltnid')
            if len(kcmgxxaltid) == 0 or len(kcmgxxaltid) > 20 or len(kcmgxxaltpid) > 20 or len(kcmgxxaltpid) == 0 or len(kcmgxxaltnid) > 20 or len(kcmgxxaltnid) == 0 or kcmgxxaltnid == kcmgxxaltid or kcmgxxaltid == kcmgxxaltpid or kcmgxxaltpid == kcmgxxaltnid:
                return render(request, 'home.html', {'func': 'kcmanage', 'usercollege': user['usercollege'], 'iskcmgxxalt': 'False', 'kcmgxxaltmsg': '信息格式错误，请重新输入！', 'anchor': 'anchor_kcmgxxalt'})
            if Course.objects.filter(courseid=kcmgxxaltid).count() == 0 or Course.objects.filter(courseid=kcmgxxaltnid).count() == 0:
                return render(request, 'home.html', {'func': 'kcmanage', 'usercollege': user['usercollege'], 'iskcmgxxalt': 'False', 'kcmgxxaltmsg': '课程不存在，请重新输入！', 'anchor': 'anchor_kcmgxxalt'})
            xxcs = Course.objects.filter(courseid=kcmgxxaltid).values()[0]
            if request.session.get('usertype') == 1 and xxcs['coursecollege'] != user['usercollege'] or request.session.get('usertype') == 2 and xxcs['teacherid'] != userid:
                return render(request, 'home.html', {'func': 'kcmanage', 'usercollege': user['usercollege'], 'iskcmgxxalt': 'False', 'kcmgxxaltmsg': '非管理范围内课程，权限不足，请重新输入！', 'anchor': 'anchor_kcmgxxalt'})
            if Prerequisite.objects.filter(courseid=kcmgxxaltid, precourseid=kcmgxxaltpid).count() == 0:
                return render(request, 'home.html', {'func': 'kcmanage', 'usercollege': user['usercollege'], 'iskcmgxxalt': 'False', 'kcmgxxaltmsg': '先修课程记录不存在，请重新输入！', 'anchor': 'anchor_kcmgxxalt'})
            if Prerequisite.objects.filter(courseid=kcmgxxaltid, precourseid=kcmgxxaltnid).count() > 0:
                return render(request, 'home.html', {'func': 'kcmanage', 'usercollege': user['usercollege'], 'iskcmgxxalt': 'False', 'kcmgxxaltmsg': '请勿重复设置先修课程！', 'anchor': 'anchor_kcmgxxalt'})
            if Course.objects.filter(courseid=kcmgxxaltid).values()[0]['isdrawlots'] == True or Course.objects.filter(courseid=kcmgxxaltnid).values()[0]['isdrawlots'] == True or (Course.objects.filter(courseid=kcmgxxaltid).values()[0]['isdrawlots'] == False and Select.objects.filter(courseid=kcmgxxaltid).count()):
                return render(request, 'home.html', {'func': 'kcmanage', 'usercollege': user['usercollege'], 'iskcmgxxalt': 'False', 'kcmgxxaltmsg': '已经开始选课，无法修改先修课程！', 'anchor': 'anchor_kcmgxxalt'})
            if Prerequisite.objects.filter(courseid=kcmgxxaltnid, precourseid=kcmgxxaltid).count() > 0 or topo(kcmgxxaltid, kcmgxxaltnid) == False:
                return render(request, 'home.html', {'func': 'kcmanage', 'usercollege': user['usercollege'], 'iskcmgxxalt': 'False', 'kcmgxxaltmsg': '产生循环依赖，请重新输入！', 'anchor': 'anchor_kcmgxxalt'})
            Prerequisite.objects.filter(
                courseid=kcmgxxaltid, precourseid=kcmgxxaltpid).update(precourseid=kcmgxxaltnid)
            return render(request, 'home.html', {'func': 'kcmanage', 'usercollege': user['usercollege'], 'iskcmgxxalt': 'True', 'kcmgxxaltmsg': '成功修改先修课程！', 'anchor': 'anchor_kcmgxxalt'})
        kcmgchart = request.GET.get('kcmgchart')
        if kcmgchart == 'True':
            class Chart:
                def __init__(self, name, num):
                    self.name = name
                    self.num = num
            ctlist = []
            cts = Course.objects.all().values()
            for cs in cts:
                name = cs['coursename']
                num = cs['studentnum']
                crt = Chart(name, num)
                ctlist.append(crt)
            return render(request, 'home.html', {'func': 'kcmanage', 'usercollege': user['usercollege'], 'iskcmgchart': 'True', 'anchor': 'anchor_kcmgchart', 'ctlist': ctlist})
        xk = request.GET.get('xk')
        if xk == 'True':
            xkid = request.GET.get('xkid')
            if len(xkid) > 20 or len(xkid) == 0:
                return render(request, 'home.html', {'func': 'selectcourse', 'isxk': 'False', 'xkmsg': '信息格式错误，请重新输入！'})
            if Course.objects.filter(courseid=xkid).count() == 0:
                return render(request, 'home.html', {'func': 'selectcourse', 'isxk': 'False', 'xkmsg': '课程不存在，请重新输入！'})
            if Student.objects.filter(studentid=userid, courseid=xkid).count() > 0 or Select.objects.filter(studentid=userid, courseid=xkid).count() > 0 and Course.objects.filter(courseid=xkid).values()[0]['isdrawlots'] == False:
                return render(request, 'home.html', {'func': 'selectcourse', 'isxk': 'False', 'xkmsg': '请勿重复选课，请重新输入！'})
            if Course.objects.filter(courseid=xkid).values()[0]['isdrawlots'] == True:
                return render(request, 'home.html', {'func': 'selectcourse', 'isxk': 'False', 'xkmsg': '课程已抽签，无法选课，请重新输入！'})
            for cs in Prerequisite.objects.filter(courseid=xkid).values():
                if Student.objects.filter(studentid=userid, courseid=cs['precourseid']).count() == 0 or Student.objects.filter(studentid=userid, courseid=cs['precourseid']).values()[0]['score'] is None:
                    return render(request, 'home.html', {'func': 'selectcourse', 'isxk': 'False', 'xkmsg': '缺少先修课，无法选课，请重新输入！'})
            sl = Select(studentid=userid, courseid=xkid)
            sl.save()
            return render(request, 'home.html', {'func': 'selectcourse', 'isxk': 'True', 'xkmsg': '成功选课！'})
        xkjl = request.GET.get('xkjl')
        if xkjl == 'True':
            class Xrec:
                def __init__(self, courseid, coursename, iszq):
                    self.courseid = courseid
                    self.coursename = coursename
                    self.iszq = iszq
            xkjllist = []
            for cs in Select.objects.filter(studentid=userid).values():
                courseid = cs['courseid']
                coursename = Course.objects.filter(courseid=courseid).values()[
                    0]['coursename']
                if Course.objects.filter(courseid=courseid).values()[
                        0]['isdrawlots'] == False:
                    iszq = '尚未抽签'
                elif Student.objects.filter(studentid=userid, courseid=courseid).count() > 0:
                    iszq = '中签'
                else:
                    iszq = '未中签'
                xc = Xrec(courseid, coursename, iszq)
                xkjllist.append(xc)
            xkjlnum = len(xkjllist)
            return render(request, 'home.html', {'func': 'selectcourse', 'isxkjl': 'True', 'xkjlnum': xkjlnum, 'xkjllist': xkjllist, 'anchor': 'anchor_xkjl'})
        cq = request.GET.get('cq')
        if cq == 'True':
            cqid = request.GET.get('cqid')
            if len(cqid) > 20 or len(cqid) == 0:
                return render(request, 'home.html', {'func': 'chouqian', 'iscq': 'False', 'cqmsg': '信息格式错误，请重新输入！'})
            if Course.objects.filter(courseid=cqid).count() == 0:
                return render(request, 'home.html', {'func': 'chouqian', 'iscq': 'False', 'cqmsg': '课程不存在，请重新输入！'})
            if Course.objects.filter(courseid=cqid).values()[0]['coursecollege'] != user['usercollege']:
                return render(request, 'home.html', {'func': 'chouqian', 'iscq': 'False', 'cqmsg': '非管理范围内课程，权限不足，请重新输入！'})
            if Course.objects.filter(courseid=cqid).values()[0]['isdrawlots'] == True:
                return render(request, 'home.html', {'func': 'chouqian', 'iscq': 'False', 'cqmsg': '请勿重复抽签，请重新输入！'})
            if Select.objects.filter(courseid=cqid).count() == 0:
                return render(request, 'home.html', {'func': 'chouqian', 'iscq': 'False', 'cqmsg': '选课人数为0，无法抽签，请重新输入！'})
            maxnum = Course.objects.filter(courseid=cqid).values()[0]['maxnum']
            slnum = Select.objects.filter(courseid=cqid).count()

            class Cqian:
                def __init__(self, courseid, coursename, studentid, studentname):
                    self.courseid = courseid
                    self.coursename = coursename
                    self.studentid = studentid
                    self.studentname = studentname
            cqlist = []
            coursename = Course.objects.filter(courseid=cqid).values()[
                0]['coursename']
            if slnum <= maxnum:
                cqnum = slnum
                for st in Select.objects.filter(courseid=cqid).values():
                    studentid = st['studentid']
                    studentname = User.objects.filter(
                        userid=studentid).values()[0]['username']
                    stu = Student(studentid=studentid, courseid=cqid)
                    stu.save()
                    cqn = Cqian(cqid, coursename, studentid, studentname)
                    cqlist.append(cqn)
            else:
                cqnum = maxnum
                tmplist = []
                for st in Select.objects.filter(courseid=cqid).values():
                    studentid = st['studentid']
                    tmplist.append(studentid)
                tmplist = sample(tmplist, maxnum)
                for st in tmplist:
                    studentname = User.objects.filter(
                        userid=st).values()[0]['username']
                    stu = Student(studentid=st, courseid=cqid)
                    stu.save()
                    cqn = Cqian(cqid, coursename, st, studentname)
                    cqlist.append(cqn)
            Course.objects.filter(courseid=cqid).update(
                isdrawlots=True, studentnum=cqnum)
            return render(request, 'home.html', {'func': 'chouqian', 'iscq': 'True', 'cqnum': cqnum, 'maxnum': maxnum, 'cqlist': cqlist})
        xkmgcx = request.GET.get('xkmgcx')
        if xkmgcx == 'True':
            xkmgcxcoursename = request.GET.get('xkmgcxcoursename')
            xkmgcxxsname = request.GET.get('xkmgcxxsname')
            xkmgcxcollege = request.GET.get('xkmgcxcollege')
            if len(xkmgcxcoursename) > 20 or len(xkmgcxxsname) > 20:
                return render(request, 'home.html', {'func': 'xkmg', 'usercollege': user['usercollege'], 'isxkmgcx': 'False', 'xkmgcxmsg': '信息格式错误，请重新输入！'})
            ccs = Course.objects.filter(coursecollege=xkmgcxcollege)
            if len(xkmgcxcoursename) > 0:
                ccs = ccs.filter(Q(coursename__contains=xkmgcxcoursename))
            ccs = ccs.values()
            xkmgcxlist = []

            class Xmgcx:
                def __init__(self, courseid, coursename, studentid, studentname):
                    self.courseid = courseid
                    self.coursename = coursename
                    self.studentid = studentid
                    self.studentname = studentname
            for cs in ccs:
                courseid = cs['courseid']
                coursename = cs['coursename']
                stu = Student.objects.filter(courseid=courseid)
                if len(xkmgcxxsname) > 0:
                    stu = stu.filter(Q(studentid__in=User.objects.filter(
                        username__contains=xkmgcxxsname)))
                stu = stu.values()
                for su in stu:
                    studentid = su['studentid']
                    studentname = User.objects.filter(
                        userid=studentid).values()[0]['username']
                    xx = Xmgcx(courseid, coursename, studentid, studentname)
                    xkmgcxlist.append(xx)
            xkmgcxnum = len(xkmgcxlist)
            return render(request, 'home.html', {'func': 'xkmg', 'usercollege': user['usercollege'], 'isxkmgcx': 'True', 'xkmgcxnum': xkmgcxnum, 'xkmgcxlist': xkmgcxlist})
        xkmgnew = request.GET.get('xkmgnew')
        if xkmgnew == 'True':
            xkmgnewcourseid = request.GET.get('xkmgnewcourseid')
            xkmgnewxsid = request.GET.get('xkmgnewxsid')
            if len(xkmgnewxsid) > 20 or len(xkmgnewxsid) == 0 or len(xkmgnewcourseid) > 20 or len(xkmgnewcourseid) == 0:
                return render(request, 'home.html', {'func': 'xkmg', 'usercollege': user['usercollege'], 'isxkmgnew': 'False', 'xkmgnewmsg': '信息格式错误，请重新输入！', 'anchor': 'anchor_xkmgnew'})
            if User.objects.filter(userid=xkmgnewxsid).count() == 0 or User.objects.filter(userid=xkmgnewxsid).values()[0]['usertype'] != 3:
                return render(request, 'home.html', {'func': 'xkmg', 'usercollege': user['usercollege'], 'isxkmgnew': 'False', 'xkmgnewmsg': '学生不存在，请重新输入！', 'anchor': 'anchor_xkmgnew'})
            if Course.objects.filter(courseid=xkmgnewcourseid).count() == 0:
                return render(request, 'home.html', {'func': 'xkmg', 'usercollege': user['usercollege'], 'isxkmgnew': 'False', 'xkmgnewmsg': '课程不存在，请重新输入！', 'anchor': 'anchor_xkmgnew'})
            if request.session.get('usertype') == 1 and Course.objects.filter(courseid=xkmgnewcourseid).values()[0]['coursecollege'] != user['usercollege']:
                return render(request, 'home.html', {'func': 'xkmg', 'usercollege': user['usercollege'], 'isxkmgnew': 'False', 'xkmgnewmsg': '非本学院课程，权限不足，请重新输入！', 'anchor': 'anchor_xkmgnew'})
            if Course.objects.filter(courseid=xkmgnewcourseid).values()[0]['isdrawlots'] == False:
                return render(request, 'home.html', {'func': 'xkmg', 'usercollege': user['usercollege'], 'isxkmgnew': 'False', 'xkmgnewmsg': '课程尚未抽签，请学生登录系统自行选课，请重新输入！', 'anchor': 'anchor_xkmgnew'})
            if Student.objects.filter(studentid=xkmgnewxsid, courseid=xkmgnewcourseid).count() > 0:
                return render(request, 'home.html', {'func': 'xkmg', 'usercollege': user['usercollege'], 'isxkmgnew': 'False', 'xkmgnewmsg': '请勿重复选课，请重新输入！', 'anchor': 'anchor_xkmgnew'})
            if Course.objects.filter(courseid=xkmgnewcourseid).values()[0]['studentnum'] == Course.objects.filter(courseid=xkmgnewcourseid).values()[0]['maxnum']:
                return render(request, 'home.html', {'func': 'xkmg', 'usercollege': user['usercollege'], 'isxkmgnew': 'False', 'xkmgnewmsg': '选课人数已达上限，无法选课，请重新输入！', 'anchor': 'anchor_xkmgnew'})
            for cs in Prerequisite.objects.filter(courseid=xkmgnewcourseid).values():
                if Student.objects.filter(studentid=xkmgnewxsid, courseid=cs['precourseid']).count() == 0 or Student.objects.filter(studentid=xkmgnewxsid, courseid=cs['precourseid']).values()[0]['score'] is None:
                    return render(request, 'home.html', {'func': 'xkmg', 'usercollege': user['usercollege'], 'isxkmgnew': 'False', 'xkmgnewmsg': '缺少先修课程，无法选课，请重新输入！', 'anchor': 'anchor_xkmgnew'})
            sl = Select(studentid=xkmgnewxsid, courseid=xkmgnewcourseid)
            sl.save()
            stu = Student(studentid=xkmgnewxsid, courseid=xkmgnewcourseid)
            stu.save()
            Course.objects.filter(courseid=xkmgnewcourseid).update(
                studentnum=Course.objects.filter(courseid=xkmgnewcourseid).values()[0]['studentnum']+1)
            return render(request, 'home.html', {'func': 'xkmg', 'usercollege': user['usercollege'], 'isxkmgnew': 'True', 'xkmgnewmsg': '成功增加选课！', 'anchor': 'anchor_xkmgnew'})
        xkmgdel = request.GET.get('xkmgdel')
        if xkmgdel == 'True':
            xkmgdelcourseid = request.GET.get('xkmgdelcourseid')
            xkmgdelxsid = request.GET.get('xkmgdelxsid')
            if len(xkmgdelxsid) > 20 or len(xkmgdelxsid) == 0 or len(xkmgdelcourseid) > 20 or len(xkmgdelcourseid) == 0:
                return render(request, 'home.html', {'func': 'xkmg', 'usercollege': user['usercollege'], 'isxkmgdel': 'False', 'xkmgdelmsg': '信息格式错误，请重新输入！', 'anchor': 'anchor_xkmgdel'})
            if request.session.get('usertype') == 1 and Course.objects.filter(courseid=xkmgdelcourseid).values()[0]['coursecollege'] != user['usercollege']:
                return render(request, 'home.html', {'func': 'xkmg', 'usercollege': user['usercollege'], 'isxkmgdel': 'False', 'xkmgdelmsg': '非本学院课程，权限不足，请重新输入！', 'anchor': 'anchor_xkmgdel'})
            if Student.objects.filter(studentid=xkmgdelxsid, courseid=xkmgdelcourseid).count() == 0:
                return render(request, 'home.html', {'func': 'xkmg', 'usercollege': user['usercollege'], 'isxkmgdel': 'False', 'xkmgdelmsg': '选课记录不存在，请重新输入！', 'anchor': 'anchor_xkmgdel'})
            Select.objects.filter(studentid=xkmgdelxsid,
                                  courseid=xkmgdelcourseid).delete()
            score = Student.objects.filter(
                studentid=xkmgdelxsid, courseid=xkmgdelcourseid).values()[0]['score']
            cs = Course.objects.filter(courseid=xkmgdelcourseid).values()[0]
            studentnum = cs['studentnum'] - 1
            Course.objects.filter(courseid=xkmgdelcourseid).update(
                studentnum=studentnum)
            Student.objects.filter(
                studentid=xkmgdelxsid, courseid=xkmgdelcourseid).delete()
            if score is not None:
                if score > 85:
                    Course.objects.filter(courseid=xkmgdelcourseid).update(
                        outstandingnum=cs['outstandingnum']-1)
                elif score > 59:
                    Course.objects.filter(courseid=xkmgdelcourseid).update(
                        goodnum=cs['goodnum']-1)
                else:
                    Course.objects.filter(courseid=xkmgdelcourseid).update(
                        failnum=cs['failnum']-1)
                stu = Student.objects.filter(courseid=xkmgdelcourseid).values()
                amt = int(0)
                peo = int(0)
                for su in stu:
                    if su['score'] is not None:
                        peo += 1
                        if su['score'] > 59:
                            amt += 1
                Course.objects.filter(
                    courseid=xkmgdelcourseid).update(passratio=amt/peo)
            return render(request, 'home.html', {'func': 'xkmg', 'usercollege': user['usercollege'], 'isxkmgdel': 'True', 'xkmgdelmsg': '成功删除选课！', 'anchor': 'anchor_xkmgdel'})
        xkmgalt = request.GET.get('xkmgalt')
        if xkmgalt == 'True':
            xkmgaltcourseid = request.GET.get('xkmgaltcourseid')
            xkmgaltncourseid = request.GET.get('xkmgaltncourseid')
            xkmgaltxsid = request.GET.get('xkmgaltxsid')
            if len(xkmgaltxsid) > 20 or len(xkmgaltxsid) == 0 or len(xkmgaltcourseid) > 20 or len(xkmgaltcourseid) == 0 or len(xkmgaltncourseid) > 20 or len(xkmgaltncourseid) == 0 or xkmgaltncourseid == xkmgaltcourseid:
                return render(request, 'home.html', {'func': 'xkmg', 'usercollege': user['usercollege'], 'isxkmgdel': 'False', 'xkmgdelmsg': '信息格式错误，请重新输入！', 'anchor': 'anchor_xkmgdel'})
            if Course.objects.filter(courseid=xkmgaltncourseid).count() == 0:
                return render(request, 'home.html', {'func': 'xkmg', 'usercollege': user['usercollege'], 'isxkmgalt': 'False', 'xkmgaltmsg': '课程不存在，请重新输入！', 'anchor': 'anchor_xkmgalt'})
            if request.session.get('usertype') == 1 and (Course.objects.filter(courseid=xkmgaltcourseid).values()[0]['coursecollege'] != user['usercollege'] or Course.objects.filter(courseid=xkmgaltncourseid).values()[0]['coursecollege'] != user['usercollege']):
                return render(request, 'home.html', {'func': 'xkmg', 'usercollege': user['usercollege'], 'isxkmgalt': 'False', 'xkmgaltmsg': '非本学院课程，权限不足，请重新输入！', 'anchor': 'anchor_xkmgalt'})
            if Student.objects.filter(studentid=xkmgaltxsid, courseid=xkmgaltcourseid).count() == 0:
                return render(request, 'home.html', {'func': 'xkmg', 'usercollege': user['usercollege'], 'isxkmgalt': 'False', 'xkmgaltmsg': '选课记录不存在，请重新输入！', 'anchor': 'anchor_xkmgalt'})
            if Course.objects.filter(courseid=xkmgaltncourseid).values()[0]['isdrawlots'] == False:
                return render(request, 'home.html', {'func': 'xkmg', 'usercollege': user['usercollege'], 'isxkmgalt': 'False', 'xkmgaltmsg': '课程尚未抽签，请学生登录系统自行选课，请重新输入！', 'anchor': 'anchor_xkmgalt'})
            if Student.objects.filter(studentid=xkmgaltxsid, courseid=xkmgaltncourseid).count() > 0:
                return render(request, 'home.html', {'func': 'xkmg', 'usercollege': user['usercollege'], 'isxkmgalt': 'False', 'xkmgaltmsg': '请勿重复选课，请重新输入！', 'anchor': 'anchor_xkmgalt'})
            if Course.objects.filter(courseid=xkmgaltncourseid).values()[0]['studentnum'] == Course.objects.filter(courseid=xkmgaltncourseid).values()[0]['maxnum']:
                return render(request, 'home.html', {'func': 'xkmg', 'usercollege': user['usercollege'], 'isxkmgalt': 'False', 'xkmgaltmsg': '选课人数已达上限，无法选课，请重新输入！', 'anchor': 'anchor_xkmgalt'})
            Select.objects.filter(studentid=xkmgaltxsid,
                                  courseid=xkmgaltcourseid).delete()
            score = Student.objects.filter(
                studentid=xkmgaltxsid, courseid=xkmgaltcourseid).values()[0]['score']
            cs = Course.objects.filter(courseid=xkmgaltcourseid).values()[0]
            studentnum = cs['studentnum'] - 1
            Course.objects.filter(courseid=xkmgaltcourseid).update(
                studentnum=studentnum)
            Student.objects.filter(
                studentid=xkmgaltxsid, courseid=xkmgaltcourseid).delete()
            if score is not None:
                if score > 85:
                    Course.objects.filter(courseid=xkmgaltcourseid).update(
                        outstandingnum=cs['outstandingnum']-1)
                elif score > 59:
                    Course.objects.filter(courseid=xkmgaltcourseid).update(
                        goodnum=cs['goodnum']-1)
                else:
                    Course.objects.filter(courseid=xkmgaltcourseid).update(
                        failnum=cs['failnum']-1)
                stu = Student.objects.filter(courseid=xkmgaltcourseid).values()
                amt = int(0)
                peo = int(0)
                for su in stu:
                    if su['score'] is not None:
                        peo += 1
                        if su['score'] > 59:
                            amt += 1
                Course.objects.filter(
                    courseid=xkmgaltcourseid).update(passratio=amt/peo)
            sl = Select(studentid=xkmgaltxsid, courseid=xkmgaltncourseid)
            sl.save()
            stu = Student(studentid=xkmgaltxsid, courseid=xkmgaltncourseid)
            stu.save()
            Course.objects.filter(courseid=xkmgaltncourseid).update(
                studentnum=Course.objects.filter(courseid=xkmgaltncourseid).values()[0]['studentnum']+1)
            return render(request, 'home.html', {'func': 'xkmg', 'usercollege': user['usercollege'], 'isxkmgalt': 'True', 'xkmgaltmsg': '成功修改选课！', 'anchor': 'anchor_xkmgalt'})
        ads = request.GET.get('ads')
        if ads == 'True':
            adscourseid = request.GET.get('adscourseid')
            adsxsid = request.GET.get('adsxsid')
            adssc = request.GET.get('adssc')
            if len(adscourseid) > 20 or len(adscourseid) == 0 or len(adsxsid) > 20 or len(adsxsid) == 0 or len(adssc) > 3 or len(adssc) == 0 or adssc.isdigit() == False or int(adssc) > 100 or int(adssc) < 0:
                return render(request, 'home.html', {'func': 'addscore', 'isads': 'False', 'adsmsg': '信息格式错误，请重新输入！'})
            if Course.objects.filter(courseid=adscourseid).values()[0]['teacherid'] != userid:
                return render(request, 'home.html', {'func': 'addscore', 'isads': 'False', 'adsmsg': '非管理范围内课程，权限不足，请重新输入！'})
            if Student.objects.filter(studentid=adsxsid, courseid=adscourseid).count() == 0:
                return render(request, 'home.html', {'func': 'addscore', 'isads': 'False', 'adsmsg': '选课记录不存在，请重新输入！'})
            if Student.objects.filter(studentid=adsxsid, courseid=adscourseid).values()[0]['score'] is not None:
                return render(request, 'home.html', {'func': 'addscore', 'isads': 'False', 'adsmsg': '请勿重复录入成绩，请重新输入！'})
            adssc = int(adssc)
            Student.objects.filter(
                studentid=adsxsid, courseid=adscourseid).update(score=adssc)
            cs = Course.objects.filter(courseid=adscourseid).values()[0]
            if cs['failnum'] is None:
                Course.objects.filter(courseid=adscourseid).update(failnum=0)
            if cs['goodnum'] is None:
                Course.objects.filter(courseid=adscourseid).update(goodnum=0)
            if cs['outstandingnum'] is None:
                Course.objects.filter(
                    courseid=adscourseid).update(outstandingnum=0)
            if adssc < 60:
                Course.objects.filter(courseid=adscourseid).update(
                    failnum=Course.objects.filter(courseid=adscourseid).values()[0]['failnum']+1)
            elif adssc < 86:
                Course.objects.filter(courseid=adscourseid).update(
                    goodnum=Course.objects.filter(courseid=adscourseid).values()[0]['goodnum']+1)
            else:
                Course.objects.filter(courseid=adscourseid).update(
                    outstandingnum=Course.objects.filter(courseid=adscourseid).values()[0]['outstandingnum']+1)
            stu = Student.objects.filter(courseid=adscourseid).values()
            amt = int(0)
            peo = int(0)
            for su in stu:
                if su['score'] is not None:
                    peo += 1
                    if su['score'] > 59:
                        amt += 1
            Course.objects.filter(
                courseid=adscourseid).update(passratio=amt/peo)
            return render(request, 'home.html', {'func': 'addscore', 'isads': 'True', 'adsmsg': '成功录入成绩！'})
        cjmgcx = request.GET.get('cjmgcx')
        if cjmgcx == 'True':
            cjmgcxcoursename = request.GET.get('cjmgcxcoursename')
            cjmgcxxsname = request.GET.get('cjmgcxxsname')
            if user['usertype'] == 0:
                cjmgcxcollege = request.GET.get('cjmgcxcollege')
            else:
                cjmgcxcollege = user['usercollege']
            if len(cjmgcxcoursename) > 20 or len(cjmgcxxsname) > 20:
                return render(request, 'home.html', {'func': 'cjmg', 'usercollege': user['usercollege'], 'iscjmgcx': 'False', 'cjmgcxmsg': '信息格式错误，请重新输入！'})
            ccs = Course.objects.filter(coursecollege=cjmgcxcollege)
            if len(cjmgcxcoursename) > 0:
                ccs = ccs.filter(Q(coursename__contains=cjmgcxcoursename))
            ccs = ccs.values()
            cjmgcxlist = []

            class Cmgcx:
                def __init__(self, courseid, coursename, studentid, studentname, score):
                    self.courseid = courseid
                    self.coursename = coursename
                    self.studentid = studentid
                    self.studentname = studentname
                    self.score = score
            for cs in ccs:
                courseid = cs['courseid']
                coursename = cs['coursename']
                stu = Student.objects.filter(courseid=courseid)
                if len(cjmgcxxsname) > 0:
                    stu = stu.filter(Q(studentid__in=User.objects.filter(
                        username__contains=cjmgcxxsname)))
                stu = stu.values()
                for su in stu:
                    studentid = su['studentid']
                    studentname = User.objects.filter(
                        userid=studentid).values()[0]['username']
                    score = su['score']
                    if score is None:
                        score = '暂无'
                    cx = Cmgcx(courseid, coursename,
                               studentid, studentname, score)
                    cjmgcxlist.append(cx)
            cjmgcxnum = len(cjmgcxlist)
            return render(request, 'home.html', {'func': 'cjmg', 'usercollege': user['usercollege'], 'iscjmgcx': 'True', 'cjmgcxnum': cjmgcxnum, 'cjmgcxlist': cjmgcxlist})
        cjmgnew = request.GET.get('cjmgnew')
        if cjmgnew == 'True':
            cjmgnewcourseid = request.GET.get('cjmgnewcourseid')
            cjmgnewxsid = request.GET.get('cjmgnewxsid')
            cjmgnewsc = request.GET.get('cjmgnewsc')
            if len(cjmgnewcourseid) > 20 or len(cjmgnewcourseid) == 0 or len(cjmgnewxsid) > 20 or len(cjmgnewxsid) == 0 or len(cjmgnewsc) > 3 or len(cjmgnewsc) == 0 or cjmgnewsc.isdigit() == False or int(cjmgnewsc) > 100 or int(cjmgnewsc) < 0:
                return render(request, 'home.html', {'func': 'cjmg', 'iscjmgnew': 'False', 'cjmgnewmsg': '信息格式错误，请重新输入！', 'anchor': 'anchor_cjmgnew'})
            if user['usertype'] == 1 and Course.objects.filter(courseid=cjmgnewcourseid).values()[0]['coursecollege'] != user['usercollege']:
                return render(request, 'home.html', {'func': 'cjmg', 'iscjmgnew': 'False', 'cjmgnewmsg': '非管理范围内课程，权限不足，请重新输入！', 'anchor': 'anchor_cjmgnew'})
            if Student.objects.filter(studentid=cjmgnewxsid, courseid=cjmgnewcourseid).count() == 0:
                return render(request, 'home.html', {'func': 'cjmg', 'iscjmgnew': 'False', 'cjmgnewmsg': '选课记录不存在，请重新输入！', 'anchor': 'anchor_cjmgnew'})
            if Student.objects.filter(studentid=cjmgnewxsid, courseid=cjmgnewcourseid).values()[0]['score'] is not None:
                return render(request, 'home.html', {'func': 'cjmg', 'iscjmgnew': 'False', 'cjmgnewmsg': '请勿重复录入成绩，请重新输入！', 'anchor': 'anchor_cjmgnew'})
            cjmgnewsc = int(cjmgnewsc)
            Student.objects.filter(
                studentid=cjmgnewxsid, courseid=cjmgnewcourseid).update(score=cjmgnewsc)
            cs = Course.objects.filter(courseid=cjmgnewcourseid).values()[0]
            if cs['failnum'] is None:
                Course.objects.filter(
                    courseid=cjmgnewcourseid).update(failnum=0)
            if cs['goodnum'] is None:
                Course.objects.filter(
                    courseid=cjmgnewcourseid).update(goodnum=0)
            if cs['outstandingnum'] is None:
                Course.objects.filter(
                    courseid=cjmgnewcourseid).update(outstandingnum=0)
            if cjmgnewsc < 60:
                Course.objects.filter(courseid=cjmgnewcourseid).update(
                    failnum=Course.objects.filter(courseid=cjmgnewcourseid).values()[0]['failnum']+1)
            elif cjmgnewsc < 86:
                Course.objects.filter(courseid=cjmgnewcourseid).update(
                    goodnum=Course.objects.filter(courseid=cjmgnewcourseid).values()[0]['goodnum']+1)
            else:
                Course.objects.filter(courseid=cjmgnewcourseid).update(
                    outstandingnum=Course.objects.filter(courseid=cjmgnewcourseid).values()[0]['outstandingnum']+1)
            stu = Student.objects.filter(courseid=cjmgnewcourseid).values()
            amt = int(0)
            peo = int(0)
            for su in stu:
                if su['score'] is not None:
                    peo += 1
                    if su['score'] > 59:
                        amt += 1
            Course.objects.filter(
                courseid=cjmgnewcourseid).update(passratio=amt/peo)
            return render(request, 'home.html', {'func': 'cjmg', 'iscjmgnew': 'True', 'cjmgnewmsg': '成功增加成绩！', 'anchor': 'anchor_cjmgnew'})
        cjmgdel = request.GET.get('cjmgdel')
        if cjmgdel == 'True':
            cjmgdelcourseid = request.GET.get('cjmgdelcourseid')
            cjmgdelxsid = request.GET.get('cjmgdelxsid')
            if len(cjmgdelcourseid) > 20 or len(cjmgdelcourseid) == 0 or len(cjmgdelxsid) > 20 or len(cjmgdelxsid) == 0:
                return render(request, 'home.html', {'func': 'cjmg', 'iscjmgdel': 'False', 'cjmgdelmsg': '信息格式错误，请重新输入！', 'anchor': 'anchor_cjmgdel'})
            if user['usertype'] == 1 and Course.objects.filter(courseid=cjmgdelcourseid).values()[0]['coursecollege'] != user['usercollege']:
                return render(request, 'home.html', {'func': 'cjmg', 'iscjmgdel': 'False', 'cjmgdelmsg': '非管理范围内课程，权限不足，请重新输入！', 'anchor': 'anchor_cjmgdel'})
            if Student.objects.filter(studentid=cjmgdelxsid, courseid=cjmgdelcourseid).count() == 0 or Student.objects.filter(studentid=cjmgdelxsid, courseid=cjmgdelcourseid).values()[0]['score'] is None:
                return render(request, 'home.html', {'func': 'cjmg', 'iscjmgdel': 'False', 'cjmgdelmsg': '成绩不存在，请重新输入！', 'anchor': 'anchor_cjmgdel'})
            score = Student.objects.filter(
                studentid=cjmgdelxsid, courseid=cjmgdelcourseid).values()[0]['score']
            cs = Course.objects.filter(courseid=cjmgdelcourseid).values()[0]
            if score > 85:
                Course.objects.filter(courseid=cjmgdelcourseid).update(
                    outstandingnum=cs['outstandingnum']-1)
            elif score > 59:
                Course.objects.filter(courseid=cjmgdelcourseid).update(
                    goodnum=cs['goodnum']-1)
            else:
                Course.objects.filter(courseid=cjmgdelcourseid).update(
                    failnum=cs['failnum']-1)
            Student.objects.filter(
                studentid=cjmgdelxsid, courseid=cjmgdelcourseid).update(score=None)
            stu = Student.objects.filter(courseid=cjmgdelcourseid).values()
            amt = int(0)
            peo = int(0)
            for su in stu:
                if su['score'] is not None:
                    peo += 1
                    if su['score'] > 59:
                        amt += 1
            Course.objects.filter(
                courseid=cjmgdelcourseid).update(passratio=amt/peo)
            return render(request, 'home.html', {'func': 'cjmg', 'iscjmgdel': 'True', 'cjmgdelmsg': '成功删除成绩！', 'anchor': 'anchor_cjmgdel'})
        cjmgalt = request.GET.get('cjmgalt')
        if cjmgalt == 'True':
            cjmgaltcourseid = request.GET.get('cjmgaltcourseid')
            cjmgaltxsid = request.GET.get('cjmgaltxsid')
            cjmgaltsc = request.GET.get('cjmgaltsc')
            if len(cjmgaltcourseid) > 20 or len(cjmgaltcourseid) == 0 or len(cjmgaltxsid) > 20 or len(cjmgaltxsid) == 0 or len(cjmgaltsc) > 3 or len(cjmgaltsc) == 0 or cjmgaltsc.isdigit() == False or int(cjmgaltsc) > 100 or int(cjmgaltsc) < 0:
                return render(request, 'home.html', {'func': 'cjmg', 'iscjmgalt': 'False', 'cjmgaltmsg': '信息格式错误，请重新输入！', 'anchor': 'anchor_cjmgalt'})
            if user['usertype'] == 1 and Course.objects.filter(courseid=cjmgaltcourseid).values()[0]['coursecollege'] != user['usercollege']:
                return render(request, 'home.html', {'func': 'cjmg', 'iscjmgalt': 'False', 'cjmgaltmsg': '非管理范围内课程，权限不足，请重新输入！', 'anchor': 'anchor_cjmgalt'})
            if Student.objects.filter(studentid=cjmgaltxsid, courseid=cjmgaltcourseid).count() == 0 or Student.objects.filter(studentid=cjmgaltxsid, courseid=cjmgaltcourseid).values()[0]['score'] is None:
                return render(request, 'home.html', {'func': 'cjmg', 'iscjmgalt': 'False', 'cjmgaltmsg': '成绩不存在，请重新输入！', 'anchor': 'anchor_cjmgalt'})
            cjmgaltsc = int(cjmgaltsc)
            score = Student.objects.filter(
                studentid=cjmgaltxsid, courseid=cjmgaltcourseid).values()[0]['score']
            if score == cjmgaltsc:
                return render(request, 'home.html', {'func': 'cjmg', 'iscjmgalt': 'False', 'cjmgaltmsg': '成绩未修改，请重新输入！', 'anchor': 'anchor_cjmgalt'})
            cs = Course.objects.filter(courseid=cjmgaltcourseid).values()[0]
            if score > 85:
                Course.objects.filter(courseid=cjmgaltcourseid).update(
                    outstandingnum=cs['outstandingnum']-1)
            elif score > 59:
                Course.objects.filter(courseid=cjmgaltcourseid).update(
                    goodnum=cs['goodnum']-1)
            else:
                Course.objects.filter(courseid=cjmgaltcourseid).update(
                    failnum=cs['failnum']-1)
            Student.objects.filter(
                studentid=cjmgaltxsid, courseid=cjmgaltcourseid).update(score=cjmgaltsc)
            if cjmgaltsc < 60:
                Course.objects.filter(courseid=cjmgaltcourseid).update(
                    failnum=Course.objects.filter(courseid=cjmgaltcourseid).values()[0]['failnum']+1)
            elif cjmgaltsc < 86:
                Course.objects.filter(courseid=cjmgaltcourseid).update(
                    goodnum=Course.objects.filter(courseid=cjmgaltcourseid).values()[0]['goodnum']+1)
            else:
                Course.objects.filter(courseid=cjmgaltcourseid).update(
                    outstandingnum=Course.objects.filter(courseid=cjmgaltcourseid).values()[0]['outstandingnum']+1)
            stu = Student.objects.filter(courseid=cjmgaltcourseid).values()
            amt = int(0)
            peo = int(0)
            for su in stu:
                if su['score'] is not None:
                    peo += 1
                    if su['score'] > 59:
                        amt += 1
            Course.objects.filter(
                courseid=cjmgaltcourseid).update(passratio=amt/peo)
            return render(request, 'home.html', {'func': 'cjmg', 'iscjmgalt': 'True', 'cjmgaltmsg': '成功修改成绩！', 'anchor': 'anchor_cjmgalt'})
        xzkj = request.GET.get('xzkj')
        if xzkj == 'True':
            kjlist = []

            class Kj:
                def __init__(self, courseid, coursename, kjname, link):
                    self.courseid = courseid
                    self.coursename = coursename
                    self.kjname = kjname
                    self.link = link
            stu = Student.objects.filter(studentid=userid).values()
            for su in stu:
                courseid = su['courseid']
                coursename = Course.objects.filter(courseid=courseid).values()[
                    0]['coursename']
                cw = Courseware.objects.filter(courseid=courseid).values()
                for c in cw:
                    kjname = c['courseware']
                    link = os.path.join(settings.MEDIA_ROOT, kjname)
                    kl = Kj(courseid, coursename, kjname, link)
                    kjlist.append(kl)
            kjnum = len(kjlist)
            return render(request, 'home.html', {'func': 'xzkj', 'isxzkj': 'True', 'kjnum': kjnum, 'kjlist': kjlist})
        xzkjlink = request.GET.get('xzkjlink')
        if xzkjlink is not None:
            kj = open(xzkjlink, 'rb')
            return FileResponse(kj)

        func = request.GET.get('func')
        if func == 'myprofile':
            return render(request, 'home.html', {'func': func, 'usercollege': user['usercollege']})
        elif func == 'message':
            return render(request, 'home.html', {'func': func, 'messagenumr': messagenumr, 'messagelistr': messagelistr, 'messagenums': messagenums, 'messagelists': messagelists})
        elif func == 'xsmanage':
            return render(request, 'home.html', {'func': func, 'usercollege': user['usercollege']})
        elif func == 'jsmanage':
            return render(request, 'home.html', {'func': func, 'usercollege': user['usercollege']})
        elif func == 'findcourse':
            return render(request, 'home.html', {'func': func})
        elif func == 'kcmanage':
            return render(request, 'home.html', {'func': func, 'usercollege': user['usercollege']})
        elif func == 'selectcourse':
            return render(request, 'home.html', {'func': func})
        elif func == 'mycourse':
            myc = Student.objects.filter(studentid=userid).values()

            class Mcourse:
                def __init__(self, courseid, coursename, score):
                    self.courseid = courseid
                    self.coursename = coursename
                    self.score = score
            mclist = []
            for mc in myc:
                courseid = mc['courseid']
                coursename = Course.objects.filter(courseid=courseid).values()[
                    0]['coursename']
                score = mc['score']
                if score is None:
                    score = '暂无'
                mce = Mcourse(courseid, coursename, score)
                mclist.append(mce)
            mcnum = len(mclist)
            return render(request, 'home.html', {'func': func, 'mcnum': mcnum, 'mclist': mclist})
        elif func == 'chouqian':
            return render(request, 'home.html', {'func': func})
        elif func == 'xkmg':
            return render(request, 'home.html', {'func': func, 'usercollege': user['usercollege']})
        elif func == 'addscore':
            return render(request, 'home.html', {'func': func})
        elif func == 'cjmg':
            return render(request, 'home.html', {'func': func, 'usercollege': user['usercollege']})
        elif func == 'fbkj':
            return render(request, 'home.html', {'func': func})
        elif func == 'xzkj':
            return render(request, 'home.html', {'func': func})

    if request.method == 'POST':
        fbkjid = request.POST.get('fbkjid')
        if len(fbkjid) > 20 or len(fbkjid) == 0:
            return render(request, 'home.html', {'func': 'fbkj', 'isfbkj': 'False', 'fbkjmsg': '信息格式错误，请重新输入！'})
        if Course.objects.filter(courseid=fbkjid).count() == 0:
            return render(request, 'home.html', {'func': 'fbkj', 'isfbkj': 'False', 'fbkjmsg': '课程不存在，请重新输入！'})
        if Course.objects.filter(courseid=fbkjid).values()[0]['teacherid'] != userid:
            return render(request, 'home.html', {'func': 'fbkj', 'isfbkj': 'False', 'fbkjmsg': '非管理范围内课程，权限不足，请重新输入！'})
        kj = request.FILES.get('kj')
        cw = Courseware(courseid=fbkjid, courseware=kj)
        cw.save()
        filepath = os.path.join(settings.MEDIA_ROOT, kj.name)
        with open(filepath, 'wb') as fp:
            for ck in kj.chunks():
                fp.write(ck)
        return render(request, 'home.html', {'func': 'fbkj', 'isfbkj': 'False', 'fbkjmsg': '成功发布课件！'})

    return render(request, 'home.html', {'func': func, 'usercollege': user['usercollege']})
