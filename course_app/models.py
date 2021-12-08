from django.db import models

# 建表，设置字段

class User(models.Model):  # 用户表
    userid = models.CharField(max_length=20, primary_key=True)  # 用户id
    username = models.CharField(max_length=20)  # 姓名
    password = models.CharField(max_length=20)  # 密码
    usertype = models.SmallIntegerField()
    # 用户类型 0-系统管理员 1-学院管理员 2-教师 3-学生
    usercollege = models.CharField(max_length=20)  # 学院

class Course(models.Model):  # 课程表
    courseid = models.CharField(max_length=20, primary_key=True)  # 课程id
    coursename = models.CharField(max_length=20)  # 课程名称
    teacherid = models.CharField(max_length=20)  # 教师id
    teachername = models.CharField(max_length=20)  # 教师姓名
    coursecollege = models.CharField(max_length=20)  # 开课学院
    isdrawlots = models.BooleanField(default=False)  # 是否已抽签
    maxnum = models.PositiveSmallIntegerField()  # 课堂容量
    studentnum = models.PositiveSmallIntegerField(default=0)  # 选课人数
    introduce = models.CharField(max_length=100, default='暂无')  # 课程介绍
    passratio = models.FloatField(null=True)  # 及格率
    failnum = models.PositiveSmallIntegerField(null=True)  # 不及格人数 0-59
    goodnum = models.PositiveSmallIntegerField(null=True)  # 良好人数 60-85
    outstandingnum = models.PositiveSmallIntegerField(null=True)  # 优秀人数 86-100

class Prerequisite(models.Model):  # 先修课表
    courseid = models.CharField(max_length=20)  # 课程id
    precourseid = models.CharField(max_length=20)  # 先修课程id

class Courseware(models.Model):  # 课件表
    courseid = models.CharField(max_length=20)  # 课程id
    courseware = models.FileField()  # 课件

class Message(models.Model):  # 留言表
    sentid_id = models.CharField(max_length=20)  # 发送者id
    sentname = models.CharField(max_length=20)  # 发送者姓名
    receiveid_id = models.CharField(max_length=20)  # 接收者id
    receivename = models.CharField(max_length=20)  # 接收者姓名
    messagetime = models.CharField(max_length=30)  # 留言时间
    content = models.CharField(max_length=100)  # 留言

class Student(models.Model):  # 学生表
    studentid = models.CharField(max_length=20)  # 学生id
    courseid = models.CharField(max_length=20)  # 课程id
    score = models.PositiveSmallIntegerField(null=True)  # 成绩

class Select(models.Model):  # 选课表
    studentid = models.CharField(max_length=20)  # 学生id
    courseid = models.CharField(max_length=20)  # 课程id
