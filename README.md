# NCUT-Course-System
A course selection system. There are 4 types of users in the system: students, teachers, college administrators, and system administrators.  
一个选课系统。系统中存在 4 类用户：学生、教师、学院管理员、系统管理员。

Time: 2021 Spring Semester

## Details 细节
1. The system mainly uses the `Django`, and also uses `layui` for front-end design. 系统主要使用了`Django`框架，另外使用了`layui`用于前端设计。
2. The database uses `Django models` based on `SQLite3`. 数据库使用了基于`SQLite3`的`Django 模型`。

## Functions 功能
- For all users 所有用户
    1. user query 用户查询
    2. personal basic information query 个人基本信息查询
    3. sending and receiving messages 收发留言
    4. course information query and browsing 课程信息查询与浏览
- For students 学生
    1. grades query 成绩查询
    2. course selection results query 选课结果查询
    3. downloading courseware 下载课件
    4. restriction testing of prerequisite courses 先修课限制检测 (implemented by topological sorting 通过拓扑排序实现)
    5. course selection 选课
    6. selected course query 已选课程查询
- For teachers 教师
    1. submiting course introductions 提交课程介绍
    2. uploading courseware 上传课件 (implemented by `jquery` 通过`jquery`实现)
    3. setting prerequisites restrictions 设置先修课限制
    4. updating and modifying course information 更新修改课程信息
    5. generating a list of students who have been selected for a course 生成选课中签学生名单
    6. entering course grades 录入课程成绩
    7. generating grade statistics 生成成绩统计表
- For college administrators 学院管理员
    1. additions, deletions and modifications of teachers in this college 本学院教师的增删改
    2. additions, deletions and modifications of students in this college 本学院学生的增删改
    3. additions, deletions and modifications of courses in this college 本学院课程的增删改
    4. additions, deletions, modifications and query of course selections in this college 本学院选课的增删改查
    5. additions, deletions, modifications and query of grades in this college 本学院成绩的增删改查
    6. drawing lots of course selection 选课抽签
    7. generating a list of students who have been selected for a course 生成选课中签学生名单
- For system administrators 系统管理员
    1. additions, deletions and modifications of teachers 教师的增删改
    2. additions, deletions and modifications of students 学生的增删改
    3. additions, deletions and modifications of courses 课程的增删改
    4. additions, deletions, modifications and query of course selections 选课的增删改查
    5. additions, deletions, modifications and query of grades 成绩的增删改查
    6. generating a school-wide course selection chart 生成全校选课统计图 (implemented by `Highcharts` 通过`Highcharts`实现)