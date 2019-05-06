from django.shortcuts import render, get_object_or_404, redirect, HttpResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .models import File, Channel, First_Category, Second_Category, SearchLog
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.conf import settings
import json

from pdfminer.pdfparser import  PDFParser,PDFDocument
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import LTTextBoxHorizontal,LAParams
from pdfminer.pdfinterp import PDFTextExtractionNotAllowed

import os, time
from win32com.client import Dispatch, constants, gencache, DispatchEx
import pythoncom
import shutil

import hashlib

Category_dict = {
        "编程开发":{
                        "前端开发":["AngularJS","Bootstrap","HTML5/CSS3","JavaScript","jQuery","ReactJS","Vue.js","其他"],
                        "后端开发":[".NET","ASP","C#","C/C++","Go","Java","Node.js","PHP","Python","Ruby","R语言","其他"],
                        "移动开发":["Android","iOS","微信开发","其他"],
                        "游戏开发":["Unity3D","VR虚拟现实","手游开发","3D游戏","其他"],
                        "硬件开发":["ARM开发","DSP开发","FPGA开发","硬件嵌入式","其他"],
                        "开发工具":["IDE","版本控制","自动化工具","其他"],
                        "开发测试":["功能测试","性能测试","灰盒测试","白盒测试","黑盒测试","其他"],
                        },
        "系统运维":{
                        "架构":["信息架构","网络架构","软件架构","其他"],
                        "服务器":["Apache","IIS","LightHttp","Nginx","Tomcat","其他"],
                        "操作系统":["Linux","MacOS","Unix","Windows","其他"],
                        "网络/安全":["安全技术","数据中心","网络管理","路由交换","通信技术","其他"],
                        "考试认证":["H3C认证","华为认证","微软认证","思科认证","等级考试","其他"]
                        },
        "设计·创作":{
                        "UI设计":["APP UI设计","Web UI设计","其他"],
                        "平面设计":["VI设计","摄影后期","淘宝美工","网页美工","其他"],
                        "设计软件":["3DMAX","AE","CAD","Dreamweaver","Photoshop","其他"],
                        "游戏动画":["动画设计","场景概念设计","游戏模型设计","游戏特效设计","游戏角色设计","其他"],
                        "影视后期":["后期剪辑","后期合成","影视特效","其他"]
                    },
        "云计算·大数据":{
                        "云计算":["CloudStack","Docker","IaaS","OpenStack","虚拟化","其他"],
                        "大数据":["Flume","Hadoop","HBase","Hive","Kafka","Spark","Storm","Yarn","Zookeeper","其他"],
                        "数据库":["MongoDB","MySQL","Oracle","Redis","SQL Server","其他"],
                        "云平台":["AWS","Azure","华为云","百度云","腾讯云","阿里云","其他"],
                        "人工智能":["数据分析","机器学习","深度学习","自然语言","计算机视觉","语音识别","其他"]
                        },
        "产品·运营·综合":{
                        "运营":["产品运营","内容运营","用户运营","其他"],
                        "金融风控":["投资理财","税务审计","融资并购","资产管理","其他"],
                        "互联网营销":["SEM","SEO","品牌公关","其他"]
                        },
    }

def get_pages(totalpage=1,current_page=1):
    """
    example: get_pages(10,1) result=[1,2,3,4,5]
    example: get_pages(10,9) result=[6,7,8,9,10]
    页码个数由WEB_DISPLAY_PAGE设定
    """
    WEB_DISPLAY_PAGE = 5
    front_offset = int(WEB_DISPLAY_PAGE / 2)
    if WEB_DISPLAY_PAGE % 2 == 1:
        behind_offset=front_offset
    else:
        behind_offset=front_offset -1

    if totalpage < WEB_DISPLAY_PAGE:
        return list(range(1,totalpage+1))
    elif current_page<=front_offset:
        return list(range(1,WEB_DISPLAY_PAGE+1))
    elif current_page>=totalpage-behind_offset:
        start_page=totalpage-WEB_DISPLAY_PAGE+1
        return list(range(start_page,totalpage+1))
    else:
        start_page=current_page-front_offset
        end_page=current_page+behind_offset
        return list(range(start_page,end_page+1))


class PDFConverter:
    def __init__(self, pathname, id, export='.'):
        self._handle_postfix = ['doc', 'docx', 'ppt', 'pptx', 'xls', 'xlsx']
        self._filename_list = list()
        self._export_folder = os.path.join(os.path.abspath('.'), 'pdfconver')
        if not os.path.exists(self._export_folder):
            os.mkdir(self._export_folder)
        self._enumerate_filename(pathname)
        self._id = id

    def _enumerate_filename(self, pathname):
        '''
        读取所有文件名
        '''
        full_pathname = os.path.abspath(pathname)
        if os.path.isfile(full_pathname):
            if self._is_legal_postfix(full_pathname):
                self._filename_list.append(full_pathname)
            else:
                raise TypeError('文件 {} 后缀名不合法！仅支持如下文件类型：{}。'.format(pathname, '、'.join(self._handle_postfix)))
        elif os.path.isdir(full_pathname):
            for relpath, _, files in os.walk(full_pathname):
                for name in files:
                    filename = os.path.join(full_pathname, relpath, name)
                    if self._is_legal_postfix(filename):
                        self._filename_list.append(os.path.join(filename))
        else:
            raise TypeError('文件/文件夹 {} 不存在或不合法！'.format(pathname))

    def _is_legal_postfix(self, filename):
        return filename.split('.')[-1].lower() in self._handle_postfix and not os.path.basename(filename).startswith(
            '~')

    def run_conver(self):
        '''
        进行批量处理，根据后缀名调用函数执行转换
        '''
        print('需要转换的文件数：', len(self._filename_list))
        pythoncom.CoInitialize()
        for filename in self._filename_list:
            postfix = filename.split('.')[-1].lower()
            funcCall = getattr(self, postfix)
            print('原文件：', filename)
            funcCall(filename)
        print('转换完成！')

    def doc(self, filename):
        '''
        doc 和 docx 文件转换
        '''
        #name = os.path.basename(filename).split('.')[0] + '.pdf'
        name = self._id + '.pdf'
        exportfile = os.path.join(self._export_folder, name)
        print('保存 PDF 文件：', exportfile)
        gencache.EnsureModule('{00020905-0000-0000-C000-000000000046}', 0, 8, 4)
        w = Dispatch("Word.Application")
        doc = w.Documents.Open(filename)
        doc.ExportAsFixedFormat(exportfile, constants.wdExportFormatPDF,
                                Item=constants.wdExportDocumentWithMarkup,
                                CreateBookmarks=constants.wdExportCreateHeadingBookmarks)

        w.Quit(constants.wdDoNotSaveChanges)

    def docx(self, filename):
        self.doc(filename)

    def xls(self, filename):
        '''
        xls 和 xlsx 文件转换
        '''
        #name = os.path.basename(filename).split('.')[0] + '.pdf'
        name = self._id + '.pdf'
        exportfile = os.path.join(self._export_folder, name)
        xlApp = DispatchEx("Excel.Application")
        xlApp.Visible = False
        xlApp.DisplayAlerts = 0
        books = xlApp.Workbooks.Open(filename, False)
        books.ExportAsFixedFormat(0, exportfile)
        books.Close(False)
        print('保存 PDF 文件：', exportfile)
        xlApp.Quit()

    def xlsx(self, filename):
        self.xls(filename)

    def ppt(self, filename):
        '''
        ppt 和 pptx 文件转换
        '''
        #name = os.path.basename(filename).split('.')[0] + '.pdf'
        name = self._id + '.pdf'
        exportfile = os.path.join(self._export_folder, name)
        gencache.EnsureModule('{00020905-0000-0000-C000-000000000046}', 0, 8, 4)
        p = Dispatch("PowerPoint.Application")
        ppt = p.Presentations.Open(filename, False, False, False)
        ppt.ExportAsFixedFormat(exportfile, 2, PrintRange=None)
        print('保存 PDF 文件：', exportfile)
        p.Quit()

    def pptx(self, filename):
        self.ppt(filename)


def handle_file(file, request):
    pathname = 'media/file/' + file.name
    with open(pathname, 'wb+') as destination:
        for chunk in file.chunks():
            destination.write(chunk)

    postfix = file.name.split('.')[-1].lower()
    prefix = file.name.split('.')[0].lower()

    first_category = First_Category.objects.get(name=request.POST['first_category'])
    second_category = Second_Category.objects.get(name=request.POST['second_category'], first_category=first_category)
    new_file = File.objects.create(
        name = file.name,
        file = pathname,
        title = request.POST['title'],
        description = request.POST['description'],
        second_category = second_category,
        size = str(file.size),
        uploaded_by = request.user,
        ext = postfix,
        status = 0
        )

    id = str(new_file.id)

    inputpdf = settings.PDF_DIR + id + '.pdf'

    if postfix == 'pdf':
        shutil.copyfile(pathname, inputpdf)

    elif postfix == 'doc' or postfix == 'docx' or postfix == 'ppt' or postfix == 'pptx' or postfix == 'xls' or postfix == 'xlsx':
        pdfConverter = PDFConverter(pathname, id)
        pdfConverter.run_conver()

    else:
        else2pdf(pathname.replace(' ',''), inputpdf)

    new_file.pdf_path = inputpdf
    new_file.content = parse(inputpdf)
    pdf2svg(inputpdf, id)
    new_file.MD5 = md5sum(new_file.content)
    new_file.img_path = settings.SVG_DIR + id
    new_file.page = len(os.listdir(settings.SVG_DIR+id))
    new_file.collected_by.add(request.user)
    new_file.collects = 1
    new_file.save()
    return


def pdf2svg(inputpdf, id):
    output = settings.SVG_DIR + id
    if not os.path.exists(output):
        os.mkdir(output)
    os.system(settings.P2S_DIR + inputpdf + ' ' + output)


def parse(text_path):
    '''解析PDF文本，并保存到TXT文件中'''
    fp = open(text_path, 'rb')
    # 用文件对象创建一个PDF文档分析器
    parser = PDFParser(fp)
    # 创建一个PDF文档
    doc = PDFDocument()
    # 连接分析器，与文档对象
    parser.set_document(doc)
    doc.set_parser(parser)

    # 提供初始化密码，如果没有密码，就创建一个空的字符串
    doc.initialize()

    # 检测文档是否提供txt转换，不提供就忽略
    if not doc.is_extractable:
        raise PDFTextExtractionNotAllowed
    else:
        # 创建PDF，资源管理器，来共享资源
        rsrcmgr = PDFResourceManager()
        # 创建一个PDF设备对象
        laparams = LAParams()
        device = PDFPageAggregator(rsrcmgr, laparams=laparams)
        # 创建一个PDF解释其对象
        interpreter = PDFPageInterpreter(rsrcmgr, device)

        # 循环遍历列表，每次处理一个page内容
        # doc.get_pages() 获取page列表
        content = ''

        for page in doc.get_pages():
            interpreter.process_page(page)
            # 接受该页面的LTPage对象
            layout = device.get_result()
            # 这里layout是一个LTPage对象 里面存放着 这个page解析出的各种对象
            # 一般包括LTTextBox, LTFigure, LTImage, LTTextBoxHorizontal 等等
            # 想要获取文本就获得对象的text属性，
            for x in layout:
                if (isinstance(x, LTTextBoxHorizontal)):
                    content += x.get_text()

        return content

def md5sum(file_content):
    file_md5 = hashlib.md5()
    file_md5.update(file_content.encode('utf-8'))
    return file_md5.hexdigest()

def else2pdf(pathname, inputpdf):
    print('else2pdf')
    os.system('ebook-convert ' + pathname + ' ' + inputpdf)


def home(request):
    channels = Channel.objects.all()
    file_count = File.objects.count()
    user_count = User.objects.count()
    files = File.objects.filter(status=1).order_by('-views')[0:5]
    return render(request, 'home.html', {'channels': channels, 'file_count': file_count, 'user_count': user_count, 'files': files})

def channel_files(request, cid):
    channel = get_object_or_404(Channel, id=cid)
    files = channel.get_files()
    files = files.filter(status=1)

    paginator_obj = Paginator(files, 10)
    request_page_num = request.GET.get('page', 1)
    files = paginator_obj.page(request_page_num)
    total_page_number = paginator_obj.num_pages
    page_list = get_pages(int(total_page_number), int(request_page_num))
    return render(request, 'channel_files.html', {'channel': channel, 'files': files, 'page_list': page_list})

def first_category_files(request, cid, fid):
    channel = get_object_or_404(Channel, id=cid)
    first_category = get_object_or_404(First_Category, id=fid)
    files = first_category.get_files()
    files = files.filter(status=1)

    paginator_obj = Paginator(files, 10)
    request_page_num = request.GET.get('page', 1)
    files = paginator_obj.page(request_page_num)
    total_page_number = paginator_obj.num_pages
    page_list = get_pages(int(total_page_number), int(request_page_num))
    return render(request, 'first_category_files.html', {'channel': channel, 'first_category': first_category, 'fid': int(fid), 'files': files, 'page_list': page_list})

def second_category_files(request, cid, fid, sid):
    channel = get_object_or_404(Channel, id=cid)
    first_category = get_object_or_404(First_Category, id=fid)
    second_category = get_object_or_404(Second_Category, id=sid)
    files = second_category.get_files()
    files = files.filter(status=1)

    paginator_obj = Paginator(files, 10)
    request_page_num = request.GET.get('page', 1)
    files = paginator_obj.page(request_page_num)
    total_page_number = paginator_obj.num_pages
    page_list = get_pages(int(total_page_number), int(request_page_num))

    return render(request, 'second_category_files.html', {'channel': channel, 'first_category': first_category, 'second_category': second_category, 'fid': int(fid), 'sid': int(sid),
                                                          'files': files, 'page_list': page_list})

def search(request, type, order):
    time1 = time.time()
    keyword = request.GET.get('wd')
    if type == 'all':
        name_files = File.objects.filter(name__icontains=keyword)
        content_files = File.objects.filter(content__icontains=keyword)
    else:
        type_files = File.objects.filter(ext__startswith=type)
        name_files = type_files.filter(name__icontains=keyword)
        content_files = type_files.filter(content__icontains=keyword)
    files = name_files | content_files
    files.distinct()
    files = files.filter(status=1)
    count = files.count()

    if order != 'default':
        files = files.order_by(order).reverse()

    paginator_obj = Paginator(files, 10)
    request_page_num = request.GET.get('page', 1)
    files = paginator_obj.page(request_page_num)
    total_page_number = paginator_obj.num_pages
    page_list = get_pages(int(total_page_number), int(request_page_num))

    try:
        word = SearchLog.objects.get(keyword=keyword)
    except SearchLog.DoesNotExist:
        word = SearchLog.objects.create(keyword=keyword)

    word.times += 1
    word.save()
    channels = Channel.objects.all()
    searchlogs = SearchLog.objects.order_by('-times')[0:9]
    count_all = File.objects.all().count()
    time2 = time.time()

    return render(request, 'search.html', {'type': type, 'order': order, 'channels': channels,
                                           'wd': keyword, 'files': files, 'searchlogs': searchlogs,
                                           'time': round(time2-time1, 6), 'count_all': count_all, 'count': count,
                                           'page_list': page_list})

@login_required()
def upload(request):
    if request.method == 'POST':
        print('post')
        file = request.FILES.get('file', '')
        handle_file(file, request)
        return redirect('uploaded')
    channels = Channel.objects.all()
    return render(request, 'upload.html',{'channels': channels})


def Return_First_Category_Data(request):
    channel = request.GET['Channel']
    First_Category_list = []
    for category in Category_dict[channel]:
        First_Category_list.append(category)
    return HttpResponse(json.dumps(First_Category_list))


def Return_Second_Category_Data(request):
    channel, first_category = request.GET['Channel'], request.GET['First_Category']
    Second_Category_list = Category_dict[channel][first_category]
    return HttpResponse(json.dumps(Second_Category_list))

@login_required()
def uploaded(request):
    return render(request, 'uploaded.html')

@login_required()
def user(request):
    files = File.objects.filter(uploaded_by=request.user)
    files.distinct()

    paginator_obj = Paginator(files, 10)
    request_page_num = request.GET.get('page', 1)
    files = paginator_obj.page(request_page_num)
    total_page_number = paginator_obj.num_pages
    page_list = get_pages(int(total_page_number), int(request_page_num))
    return render(request, 'user.html', {'files': files, 'page_list': page_list})

def content(request, id):
    file = get_object_or_404(File, id=id)
    file.views += 1
    file.save()
    path = file.img_path
    dirs = os.listdir(path)
    dirs.sort(key=lambda x: int(x[7:-4]))
    images = []
    for img in dirs:
        images.append('/static/svg/' + str(id) + '/' + img)
    return render(request, 'content.html', {'file': file, 'images': images[:10]})

def review(request):
    files = File.objects.filter(status=0)
    return render(request, 'review.html', {'files': files})