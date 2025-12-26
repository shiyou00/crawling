#!/usr/bin/env python3
"""
翻译模块 - 使用 Google Translate API 进行英中翻译
"""
import logging
from googletrans import Translator
import time

logger = logging.getLogger(__name__)

class NewsTranslator:
    """新闻翻译器 - 将英文新闻翻译为中文"""

    def __init__(self):
        """初始化翻译器"""
        self.translator = Translator()
        logger.info("翻译器初始化成功")

    def translate_text(self, text, src='en', dest='zh-cn', retry=3):
        """
        翻译文本

        Args:
            text: 要翻译的文本
            src: 源语言代码，默认 'en'（英文）
            dest: 目标语言代码，默认 'zh-cn'（简体中文）
            retry: 重试次数

        Returns:
            翻译后的文本，失败则返回原文
        """
        if not text or not text.strip():
            return text

        for attempt in range(retry):
            try:
                result = self.translator.translate(text, src=src, dest=dest)
                logger.debug(f"翻译成功: '{text[:50]}...' -> '{result.text[:50]}...'")
                return result.text
            except Exception as e:
                logger.warning(f"翻译失败 (尝试 {attempt + 1}/{retry}): {e}")
                if attempt < retry - 1:
                    time.sleep(1)  # 等待 1 秒后重试
                else:
                    logger.error(f"翻译最终失败，返回原文: {text[:50]}...")
                    return text

        return text

    def translate_news_item(self, news_item):
        """
        翻译单条新闻

        Args:
            news_item: 新闻字典，包含 title, summary 等字段

        Returns:
            添加了翻译字段的新闻字典
        """
        translated_item = news_item.copy()

        # 翻译标题
        if 'title' in news_item and news_item['title']:
            translated_item['title_zh'] = self.translate_text(news_item['title'])

        # 翻译摘要
        if 'summary' in news_item and news_item['summary']:
            translated_item['summary_zh'] = self.translate_text(news_item['summary'])

        # 翻译来源（如果需要）
        # if 'source' in news_item:
        #     translated_item['source_zh'] = self.translate_text(news_item['source'])

        return translated_item

    def translate_news_list(self, news_list):
        """
        批量翻译新闻列表

        Args:
            news_list: 新闻列表

        Returns:
            翻译后的新闻列表
        """
        translated_list = []
        total = len(news_list)

        logger.info(f"开始翻译 {total} 条新闻...")

        for i, news in enumerate(news_list, 1):
            logger.info(f"翻译进度: {i}/{total}")
            translated_news = self.translate_news_item(news)
            translated_list.append(translated_news)

            # 避免请求过快
            if i < total:
                time.sleep(0.5)

        logger.info(f"翻译完成: {total} 条新闻")
        return translated_list


def main():
    """测试翻译功能"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    # 测试翻译
    translator = NewsTranslator()

    test_news = {
        'source': 'Science Daily',
        'title': 'This Glowing Particle in a Laser Trap May Reveal How Lightning Begins',
        'date': '2025-11-24',
        'link': 'https://www.sciencedaily.com/releases/2025/11/251124231904.htm',
        'summary': 'Scientists have discovered new insights into lightning formation.',
    }

    print("\n原文:")
    print(f"标题: {test_news['title']}")
    print(f"摘要: {test_news['summary']}")

    translated = translator.translate_news_item(test_news)

    print("\n译文:")
    print(f"标题: {translated.get('title_zh', 'N/A')}")
    print(f"摘要: {translated.get('summary_zh', 'N/A')}")


if __name__ == '__main__':
    main()
