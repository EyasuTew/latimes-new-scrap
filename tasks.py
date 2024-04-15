from robocorp.tasks import task

from news_extractor import CategoryEnum, NewsExtractor


@task
def test():
    # if __name__ == "__main__":
    extractor = NewsExtractor(search_phrase="corona", category=CategoryEnum.ENTERTAINMENT.value)
    extractor.extract_news(3)
    extractor.store_data()