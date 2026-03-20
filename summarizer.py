#!/usr/bin/env python3
"""
内容摘要模块 - 获取新闻全文并生成摘要
"""
import logging
from bs4 import BeautifulSoup
import re

from request_manager import RequestManager
from exceptions import RequestError

logger = logging.getLogger(__name__)

class ContentSummarizer:
    """新闻内容摘要器 - 获取全文并生成摘要"""

    def __init__(self):
        """初始化摘要器"""
        self.request_manager = RequestManager()
        logger.info("摘要器初始化成功（使用 RequestManager）")

    def fetch_content(self, url, timeout=30):
        """
        获取新闻页面的完整内容

        Args:
            url: 新闻链接
            timeout: 请求超时时间（秒）

        Returns:
            新闻正文内容
        """
        try:
            response = self.request_manager.get(url)
            soup = BeautifulSoup(response.content, 'html.parser')

            # 根据不同网站提取内容
            content = self._extract_content_by_site(url, soup)
            return content

        except RequestError as e:
            logger.error(f"获取内容失败 {url}: {e}")
            return ""
        except Exception as e:
            logger.error(f"获取内容失败 {url}: {e}")
            return ""

    def _extract_content_by_site(self, url, soup):
        """
        根据不同网站的结构提取正文内容

        Args:
            url: 新闻链接
            soup: BeautifulSoup 对象

        Returns:
            正文内容
        """
        content = ""

        # Science Daily
        if 'sciencedaily.com' in url:
            article = soup.find('div', id='text')
            if article:
                # 提取所有段落
                paragraphs = article.find_all('p')
                content = '\n\n'.join([p.get_text(strip=True) for p in paragraphs])

        # Buffalo University
        elif 'buffalo.edu' in url:
            # Buffalo 的主要内容在 div.text.parbase.section 中
            # 查找所有这样的 div，通常第一个或后面几个包含主要内容
            text_divs = soup.find_all('div', class_=lambda x: x and 'text' in x and 'parbase' in x)

            paragraphs = []
            for text_div in text_divs:
                # 跳过图片说明等较短的段落
                div_paragraphs = text_div.find_all('p')
                for p in div_paragraphs:
                    text = p.get_text(strip=True)
                    # 只保留长度大于 50 的段落（过滤掉作者、日期等信息）
                    if len(text) > 50:
                        paragraphs.append(text)

            if paragraphs:
                content = '\n\n'.join(paragraphs)
            else:
                # 备用方案：查找 article 或 div.content
                article = soup.find('article') or soup.find('div', class_='content')
                if article:
                    paragraphs = article.find_all('p')
                    content = '\n\n'.join([p.get_text(strip=True) for p in paragraphs])

        # IQM
        elif 'meetiqm.com' in url:
            # IQM 使用 Elementor 框架，内容在 div.elementor 中
            elementor_divs = soup.find_all('div', class_='elementor')

            paragraphs = []
            for div in elementor_divs:
                div_paragraphs = div.find_all('p')
                for p in div_paragraphs:
                    text = p.get_text(strip=True)
                    # 过滤掉短段落和可能的导航/元数据
                    if len(text) > 50:
                        paragraphs.append(text)

            if paragraphs:
                content = '\n\n'.join(paragraphs)
            else:
                # 备用方案：查找 article 或 div.entry-content
                article = soup.find('article') or soup.find('div', class_='entry-content')
                if article:
                    paragraphs = article.find_all('p')
                    content = '\n\n'.join([p.get_text(strip=True) for p in paragraphs])

        # J-PARC
        elif 'j-parc.jp' in url:
            # J-PARC 内容在 div.main-contents 中
            main_contents = soup.find('div', class_='main-contents')
            if main_contents:
                paragraphs = main_contents.find_all('p')
                content = '\n\n'.join([p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 30])

        # ICON Build
        elif 'iconbuild.com' in url:
            # ICON Build 内容在 main.content 或 article 中
            main_content = soup.find('main', class_='content') or soup.find('article')
            if main_content:
                paragraphs = main_content.find_all('p')
                content = '\n\n'.join([p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 30])

        # BioMADE
        elif 'biomade.org' in url:
            # BioMADE 内容在 article 或 div.blog-item-content 中
            article = soup.find('article') or soup.find('div', class_='blog-item-content-wrapper')
            if article:
                paragraphs = article.find_all('p')
                content = '\n\n'.join([p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 30])

        # BBEU (Bio Base Europe)
        elif 'bbeu.org' in url:
            # BBEU 内容在 div#content 或 article 中
            main_content = soup.find('div', id='content') or soup.find('article')
            if main_content:
                paragraphs = main_content.find_all('p')
                content = '\n\n'.join([p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 30])

        # QB3
        elif 'qb3.org' in url:
            # QB3 内容在 article 或 div.post-content 中
            article = soup.find('article') or soup.find('div', class_='post-content')
            if article:
                paragraphs = article.find_all('p')
                content = '\n\n'.join([p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 30])

        # SOSV
        elif 'sosv.com' in url:
            # SOSV 内容在 article 或 div.entry-content 中
            article = soup.find('article') or soup.find('div', class_='entry-content')
            if article:
                paragraphs = article.find_all('p')
                content = '\n\n'.join([p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 30])

        # TII
        elif 'tii.ae' in url:
            # TII 内容在 article 标签中
            article = soup.find('article')
            if article:
                paragraphs = article.find_all('p')
                content = '\n\n'.join([p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 30])

        # QTEP (CSIC)
        elif 'qtep.csic.es' in url:
            # QTEP 内容在 article 或 div.entry-content 中
            article = soup.find('article') or soup.find('div', class_='entry-content')
            if article:
                paragraphs = article.find_all('p')
                content = '\n\n'.join([p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 30])

        # QIA (Quantum Internet Alliance)
        elif 'quantuminternetalliance.org' in url:
            # QIA 内容在 div.c-content 中
            content_div = soup.find('div', class_='c-content')
            if content_div:
                paragraphs = content_div.find_all('p')
                content = '\n\n'.join([p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 30])

        # QIH (Quantum Technology Innovation Hubs - RIKEN)
        elif 'qih.riken.jp' in url:
            content = '[聚合页面] 请查看原文链接获取详细内容'

        # CERN QTI (Quantum Technology Initiative)
        elif 'quantum.cern' in url:
            article = soup.find('div', class_='news-node-full-content-left') or soup.find('article') or soup.find('div', class_='field--name-body')
            if article:
                paragraphs = article.find_all('p')
                content = '\n\n'.join([p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 30])

        # QSIP (Quantum Sweden Innovation Platform)
        elif 'qsip.se' in url:
            # QSIP uses Oxygen builder, no standard article/entry-content
            # Content is in p tags within the main content area
            main_content = soup.find('main') or soup.find('article') or soup.find('div', class_='entry-content')
            if main_content:
                paragraphs = main_content.find_all('p')
            else:
                # Fallback: get all p tags from body
                paragraphs = soup.find_all('p')
            content = '\n\n'.join([p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 30])

        # EISMEA (European Innovation Council and SMEs Executive Agency)
        elif 'eismea.ec.europa.eu' in url:
            article = soup.find('article') or soup.find('div', class_='ecl-content-item__content-block')
            if article:
                paragraphs = article.find_all('p')
                content = '\n\n'.join([p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 30])

        # ANL (Argonne National Laboratory)
        elif 'anl.gov' in url:
            article = soup.find('article') or soup.find('div', class_='node__content') or soup.find('div', class_='field--name-body')
            if article:
                paragraphs = article.find_all('p')
                content = '\n\n'.join([p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 30])

        # SciTechDaily (WordPress + SmartMag theme)
        elif 'scitechdaily.com' in url:
            article = soup.find('div', class_='main-content') or soup.find('article')
            if article:
                paragraphs = article.find_all('p')
                content = '\n\n'.join([p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 30])

        # IBM Newsroom
        elif 'newsroom.ibm.com' in url:
            article = soup.find('div', class_='wd_body') or soup.find('div', class_='wd_content')
            if article:
                paragraphs = article.find_all('p')
                content = '\n\n'.join([p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 30])

        # The Quantum Insider
        elif 'thequantuminsider.com' in url:
            article = soup.find('div', class_='elementor-widget-theme-post-content') or soup.find('article')
            if article:
                paragraphs = article.find_all('p')
                content = '\n\n'.join([p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 30])

        # Data Center Dynamics
        elif 'datacenterdynamics.com' in url:
            article = soup.find('div', class_='main-content') or soup.find('article')
            if article:
                paragraphs = article.find_all('p')
                content = '\n\n'.join([p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 30])

        # NIST
        elif 'nist.gov' in url:
            article = soup.find('div', class_='nist-page__content') or soup.find('article')
            if article:
                paragraphs = article.find_all('p')
                content = '\n\n'.join([p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 30])

        # ============ 外部新闻站点 ============

        # Wall Street Journal (WSJ)
        elif 'wsj.com' in url:
            # WSJ 文章内容在 article 或 div.article-content 中
            article = soup.find('article') or soup.find('div', class_='article-content')
            if article:
                paragraphs = article.find_all('p')
                content = '\n\n'.join([p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 30])

        # OIST
        elif 'oist.jp' in url:
            article = soup.find('article') or soup.find('div', class_='news-content')
            if article:
                paragraphs = article.find_all('p')
                content = '\n\n'.join([p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 30])

        # RIKEN
        elif 'riken.jp' in url:
            article = soup.find('article') or soup.find('div', class_='news-detail') or soup.find('div', class_='content')
            if article:
                paragraphs = article.find_all('p')
                content = '\n\n'.join([p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 30])

        # AIST
        elif 'aist.go.jp' in url:
            article = soup.find('article') or soup.find('div', class_='content') or soup.find('div', class_='news-content')
            if article:
                paragraphs = article.find_all('p')
                content = '\n\n'.join([p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 30])

        # QST
        elif 'qst.go.jp' in url:
            article = soup.find('article') or soup.find('div', class_='content')
            if article:
                paragraphs = article.find_all('p')
                content = '\n\n'.join([p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 30])

        # NICT
        elif 'nict.go.jp' in url:
            article = soup.find('article') or soup.find('div', class_='content') or soup.find('div', class_='news-content')
            if article:
                paragraphs = article.find_all('p')
                content = '\n\n'.join([p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 30])

        # BusinessWire
        elif 'businesswire.com' in url:
            # BusinessWire 内容在 div.bw-release-story 中
            article = soup.find('div', class_='bw-release-story') or soup.find('article')
            if article:
                paragraphs = article.find_all('p')
                content = '\n\n'.join([p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 30])

        # PR Newswire
        elif 'prnewswire.com' in url:
            # PRNewswire 内容在 div.release-body 或 article 中
            article = soup.find('div', class_='release-body') or soup.find('section', class_='release-body') or soup.find('article')
            if article:
                paragraphs = article.find_all('p')
                content = '\n\n'.join([p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 30])

        # GlobeNewswire
        elif 'globenewswire.com' in url:
            article = soup.find('div', class_='main-body-container') or soup.find('article')
            if article:
                paragraphs = article.find_all('p')
                content = '\n\n'.join([p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 30])

        # BioSpace
        elif 'biospace.com' in url:
            article = soup.find('div', class_='article-body') or soup.find('article')
            if article:
                paragraphs = article.find_all('p')
                content = '\n\n'.join([p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 30])

        # Fierce Biotech
        elif 'fiercebiotech.com' in url:
            article = soup.find('div', class_='article-body') or soup.find('article')
            if article:
                paragraphs = article.find_all('p')
                content = '\n\n'.join([p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 30])

        # STAT News
        elif 'statnews.com' in url:
            article = soup.find('div', class_='entry-content') or soup.find('article')
            if article:
                paragraphs = article.find_all('p')
                content = '\n\n'.join([p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 30])

        # Nature
        elif 'nature.com' in url:
            article = soup.find('div', class_='c-article-body') or soup.find('article')
            if article:
                paragraphs = article.find_all('p')
                content = '\n\n'.join([p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 30])

        # 通用方法：如果以上都没找到
        if not content:
            # 尝试查找 article 标签
            article = soup.find('article')
            if article:
                paragraphs = article.find_all('p')
                content = '\n\n'.join([p.get_text(strip=True) for p in paragraphs])

        # 清理内容
        if content:
            content = self._clean_content(content)

        return content

    def _clean_content(self, text):
        """
        清理文本内容

        Args:
            text: 原始文本

        Returns:
            清理后的文本
        """
        # 删除多余空白
        text = re.sub(r'\s+', ' ', text)
        # 删除特殊字符
        text = re.sub(r'[\r\n\t]+', '\n', text)
        # 删除多余换行
        text = re.sub(r'\n+', '\n\n', text)

        return text.strip()

    def generate_summary(self, content, max_sentences=3):
        """
        生成简单摘要（提取前几个句子）

        Args:
            content: 正文内容
            max_sentences: 最多提取的句子数

        Returns:
            摘要文本
        """
        if not content:
            return ""

        # 按句子分割（简单方法）
        sentences = re.split(r'[.!?]\s+', content)

        # 过滤空句子
        sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 20]

        # 取前 N 个句子
        summary_sentences = sentences[:max_sentences]

        # 重新组合，确保每个句子以句号结尾
        summary = '. '.join(summary_sentences)
        if summary and not summary.endswith('.'):
            summary += '.'

        return summary

    def process_news_item(self, news_item, fetch_full_content=True):
        """
        处理单条新闻，获取内容和摘要

        Args:
            news_item: 新闻字典
            fetch_full_content: 是否获取完整内容

        Returns:
            添加了内容和摘要的新闻字典
        """
        processed_item = news_item.copy()

        # 如果已有摘要且不需要获取全文，直接返回
        if 'summary' in news_item and news_item['summary'] and not fetch_full_content:
            return processed_item

        # 获取新闻链接
        link = news_item.get('link', '')
        if not link:
            logger.warning("新闻缺少链接，无法获取内容")
            return processed_item

        logger.info(f"获取新闻内容: {link}")

        # 获取完整内容
        full_content = self.fetch_content(link)

        if full_content:
            processed_item['full_content'] = full_content

            # 如果没有摘要，生成摘要
            if not news_item.get('summary'):
                summary = self.generate_summary(full_content)
                processed_item['summary'] = summary
                logger.info(f"生成摘要: {summary[:100]}...")
        else:
            # 无法获取内容时，标注为外部链接
            if not news_item.get('summary'):
                processed_item['summary'] = "[外部链接] 内容需访问原文查看"
            processed_item['external_link'] = True

        return processed_item

    def process_news_list(self, news_list, fetch_full_content=True):
        """
        批量处理新闻列表

        Args:
            news_list: 新闻列表
            fetch_full_content: 是否获取完整内容

        Returns:
            处理后的新闻列表
        """
        processed_list = []
        total = len(news_list)

        logger.info(f"开始处理 {total} 条新闻...")

        for i, news in enumerate(news_list, 1):
            logger.info(f"处理进度: {i}/{total}")
            processed_news = self.process_news_item(news, fetch_full_content)
            processed_list.append(processed_news)

        logger.info(f"处理完成: {total} 条新闻")
        return processed_list


def main():
    """测试摘要功能"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    summarizer = ContentSummarizer()

    # 测试新闻
    test_news = {
        'source': 'Science Daily',
        'title': 'This Glowing Particle in a Laser Trap May Reveal How Lightning Begins',
        'date': '2025-11-24',
        'link': 'https://www.sciencedaily.com/releases/2025/11/251124231904.htm',
    }

    print("\n测试新闻:")
    print(f"标题: {test_news['title']}")
    print(f"链接: {test_news['link']}")

    processed = summarizer.process_news_item(test_news)

    print(f"\n摘要: {processed.get('summary', 'N/A')}")
    print(f"\n全文长度: {len(processed.get('full_content', ''))} 字符")


if __name__ == '__main__':
    main()
