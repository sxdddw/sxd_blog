from django.http import HttpResponse
from django.shortcuts import render,redirect
from django.http import HttpResponse
# Create your views here.

from django.views import View
from .models import ArticlePost, ArticleColumn
import markdown
from .forms import ArticlePostForm
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
#分页模块
from django.core.paginator import Paginator
from django.db.models import Q
from comment.models import Comment
from comment.forms import CommentForm
def article_list(request):
    # 从 url 中提取查询参数
    search = request.GET.get('search')
    order = request.GET.get('order')
    column = request.GET.get('column')
    tag = request.GET.get('tag')

    # 初始化查询集
    article_list = ArticlePost.objects.all()

    # 搜索查询集
    if search:
        article_list = article_list.filter(
            Q(title__icontains=search) |
            Q(body__icontains=search)
        )
    else:
        search = ''

    # 栏目查询集
    if column is not None and column.isdigit():
        article_list = article_list.filter(column=column)

    # 标签查询集
    if tag and tag != 'None':
        article_list = article_list.filter(tags__name__in=[tag])

    # 查询集排序
    if order == 'total_views':
        article_list = article_list.order_by('-total_views')

    paginator = Paginator(article_list, 3)
    page = request.GET.get('page')
    articles = paginator.get_page(page)

    # 需要传递给模板（templates）的对象
    context = {
        'articles': articles,
        'order': order,
        'search': search,
        'column': column,
        'tag': tag,
    }

    return render(request, 'article/list.html', context)

def article_detail(request,id):
    #取出相应文章
    article = ArticlePost.objects.get(id = id)
    md = markdown.Markdown(
        extensions=[
            'markdown.extensions.extra',
            'markdown.extensions.codehilite',
            'markdown.extensions.toc',
        ]
    )
    comments = Comment.objects.filter(article=id)
    comment_form = CommentForm()
    article.body = md.convert(article.body)

    article.total_views += 1
    article.save(update_fields=['total_views'])
    context = {'article':article,
               'toc': md.toc,
               'comments': comments,
               'comment_form': comment_form
               }
    return render(request,'article/detail.html',context)

@login_required(login_url='/userprofile/login/')
def article_create(request):
    if request.method == 'POST':
        #将提交的数据赋值到表单实列中
        article_post_form  = ArticlePostForm(request.POST, request.FILES)
        #判断提交的数据是否满足模型的要求：
        if article_post_form.is_valid():
            #保存数据，暂时不提交到数据库中
            new_article = article_post_form.save(commit=False)
            # 指定数据库中 id=1 的用户为作者\
            new_article.author = User.objects.get(id=request.user.id)
            #将新文章保存到数据库中
            if request.POST['column'] != 'none':
                new_article.column = ArticleColumn.objects.get(id=request.POST['column'])
            new_article.save()
            article_post_form.save_m2m()
            return redirect("article:article_list")
        else:
            return HttpResponse("表单内容有误，请重新输入！")
    #如果用户请求获取数据
    else:
        #创建表单类实例
        article_post_form = ArticlePostForm()
        columns = ArticleColumn.objects.all()
        context = {'article_post_form':article_post_form,'columns': columns}
        return render(request,'article/create.html',context)
def article_delete(request,id):
    #根据id获取需要删除的内容
    article = ArticlePost.objects.get(id=id)
    #调用delete方法来删除文章
    article.delete()
    #完成后返回主页
    return redirect('article:article_list')
@login_required(login_url='/userprofile/login/')
def article_update(request,id):
    #拿到要修改的文章
    article = ArticlePost.objects.get(id = id)
    #判断用户是否为post提交表单数据
    if request.user != article.author:
        return HttpResponse("抱歉，你无权修改这篇文章。")
    if request.method == 'POST':
        #将提交的数据赋值到表单实例中
        article_post_form = ArticlePostForm(data=request.POST)
        if article_post_form.is_valid():
            #保存新写入的字段信息
            article.title = request.POST['title']
            article.body = request.POST['body']
            if request.POST['column'] != 'none':
                article.column = ArticleColumn.objects.get(id=request.POST['column'])
            else:
                article.column = None
            if request.FILES.get('avatar'):
                article.avatar = request.FILES.get('avatar')
            article.tags.set(*request.POST.get('tags').split(','), clear=True)
            article.save()
            #完成后返回到修改后的文章，需要传入文章的id值
            return redirect('article:article_detail',id =id)
        else:
            return HttpResponse("表单信息有误,请重新填写")
    else:
        columns = ArticleColumn.objects.all()
        article_post_form = ArticlePostForm()
        context = {'article':article,
                   'article_post_form':article_post_form,
                   'columns': columns,
                   'tags': ','.join([x for x in article.tags.names()])
                   }
        #将相应返回到模板中
        return render(request,'article/update.html',context)
def test(request):
    return render(request,'author.html')
class IncreaseLikesView(View):
    def post(self, request, *args, **kwargs):
        article = ArticlePost.objects.get(id=kwargs.get('id'))
        article.likes += 1
        article.save()
        return HttpResponse('success')
