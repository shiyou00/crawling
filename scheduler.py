"""
定时任务调度器
使用 cron 表达式实现每天定时采集
"""
import time
import schedule
from datetime import datetime, timedelta
from main import NewsAggregator
from logger import setup_logger


logger = setup_logger('scheduler')


def daily_crawl_job():
    """每天执行的采集任务"""
    logger.info("=" * 60)
    logger.info("开始执行定时采集任务")
    logger.info("=" * 60)

    try:
        # 采集昨天的新闻
        yesterday = datetime.now() - timedelta(days=1)
        aggregator = NewsAggregator()
        result = aggregator.crawl_yesterday_news(yesterday)

        # 保存结果
        filepath = aggregator.save_to_json(result)

        logger.info(f"采集完成! 共采集 {result['total_count']} 条新闻")
        logger.info(f"结果已保存到: {filepath}")

        # 打印摘要
        aggregator.print_summary(result)

    except Exception as e:
        logger.error(f"采集任务执行失败: {e}", exc_info=True)


def run_scheduler(schedule_time="02:00"):
    """
    运行定时调度器

    Args:
        schedule_time: 每天执行的时间，格式 HH:MM，默认凌晨2点
    """
    logger.info(f"调度器启动，每天 {schedule_time} 执行采集任务")

    # 设置每天定时任务
    schedule.every().day.at(schedule_time).do(daily_crawl_job)

    # 保持运行
    while True:
        schedule.run_pending()
        time.sleep(60)  # 每分钟检查一次


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='新闻采集定时任务')
    parser.add_argument(
        '--time',
        type=str,
        default='02:00',
        help='每天执行时间 (格式: HH:MM)，默认 02:00'
    )
    parser.add_argument(
        '--run-now',
        action='store_true',
        help='立即执行一次采集任务'
    )

    args = parser.parse_args()

    if args.run_now:
        logger.info("立即执行采集任务")
        daily_crawl_job()
    else:
        run_scheduler(args.time)
