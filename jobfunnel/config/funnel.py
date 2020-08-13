"""Config object to run JobFunnel
"""
import logging
from typing import Optional, List, Dict, Any
import os

# from jobfunnel.backend.scrapers.base import BaseScraper CYCLICAL!
from jobfunnel.config import BaseConfig, ProxyConfig, SearchConfig, DelayConfig
from jobfunnel.resources import Locale, Provider, BS4_PARSER

from jobfunnel.backend.scrapers.registry import (
    SCRAPER_FROM_LOCALE, DRIVEN_SCRAPER_FROM_LOCALE
)

class JobFunnelConfig(BaseConfig):
    """Master config containing all the information we need to run jobfunnel
    """

    def __init__(self,
                 master_csv_file: str,
                 user_block_list_file: str,
                 duplicates_list_file: str,
                 cache_folder: str,
                 search_config: SearchConfig,
                 log_file: str,
                 log_level: Optional[int] = logging.INFO,
                 no_scrape: Optional[bool] = False,
                 recover_from_cache: Optional[bool] = False,
                 bs4_parser: Optional[str] = BS4_PARSER,
                 return_similar_results: Optional[bool] = False,
                 delay_config: Optional[DelayConfig] = None,
                 proxy_config: Optional[ProxyConfig] = None,
                 web_driven_scraping: Optional[bool] = False) -> None:
        """Init a config that determines how we will scrape jobs from Scrapers
        and how we will update CSV and filtering lists

        TODO: we might want to make a RunTimeConfig with the flags etc.

        Args:
            master_csv_file (str): path to the .csv file that user interacts w/
            user_block_list_file (str): path to a JSON that contains jobs user
                has decided to omit from their .csv file (i.e. archive status)
            duplicates_list_file (str): path to a JSON that contains jobs
                which TFIDF has identified to be duplicates of an existing job
            cache_folder (str): folder where all scrape data will be stored
            search_config (SearchConfig): SearchTerms config which contains the
                desired job search information (i.e. keywords)
            log_file (str): file to log all logger calls to
            log_level (int): level to log at, use 10 logging.DEBUG for more data
            no_scrape (Optional[bool], optional): If True, will not scrape data
                at all, instead will only update filters and CSV. Defaults to
                False.
            recover_from_cache (Optional[bool], optional): if True, build the
                master CSV file from the contents of all the cache files inside
                self.cache_folder. NOTE: respects the block list. not in YAML.
            bs4_parser (Optional[str], optional): the parser to use for BS4.
            return_similar_resuts (Optional[bool], optional): If True, we will
                ask the job provider to provide more loosely-similar results for
                our search queries. NOTE: only a thing for indeed rn.
            delay_config (Optional[DelayConfig], optional): delay config object.
                Defaults to a default delay config object.
            proxy_config (Optional[ProxyConfig], optional): proxy config object.
                 Defaults to None, which will result in no proxy being used
            web_driven_scraping (Optional[bool], optional): use web-driven
                scraper implementation if available. NOTE: beta feature!
        """
        self.master_csv_file = master_csv_file
        self.user_block_list_file = user_block_list_file
        self.duplicates_list_file = duplicates_list_file
        self.cache_folder = cache_folder
        self.search_config = search_config
        self.log_file = log_file
        self.log_level = log_level
        self.no_scrape = no_scrape
        self.bs4_parser = bs4_parser  # TODO: add to config
        self.recover_from_cache = recover_from_cache
        self.return_similar_results = return_similar_results
        self.web_driven_scraping = web_driven_scraping
        if not delay_config:
            # We will always use a delay config to be respectful
            self.delay_config = DelayConfig()
        else:
            self.delay_config = delay_config
        self.proxy_config = proxy_config

        # Create folder that out output files are within, if it doesn't exist
        for path_attr in [self.master_csv_file, self.user_block_list_file,
                          self.cache_folder]:
            if path_attr:
                output_dir = os.path.dirname(os.path.abspath(path_attr))
                if not os.path.exists(output_dir):
                    os.makedirs(output_dir)

        self.validate()

    @property
    def scrapers(self) -> List['BaseScraper']:
        """All the compatible scrapers for the provider_name
        """
        scrapers = []  # type: List[BaseScraper]
        for pr in self.search_config.providers:
            if self.web_driven_scraping and pr in DRIVEN_SCRAPER_FROM_LOCALE:
                scrapers.append(
                    DRIVEN_SCRAPER_FROM_LOCALE[pr][self.search_config.locale]
                )
            elif pr in SCRAPER_FROM_LOCALE:
                scrapers.append(
                    SCRAPER_FROM_LOCALE[pr][self.search_config.locale]
                )
            else:
                raise ValueError(
                    f"No scraper available for unknown provider {pr}"
                )
        return scrapers

    @property
    def scraper_names(self) -> str:
        """User-readable names of the scrapers we will be running
        """
        return [s.__name__ for s in self.scrapers]

    def create_dirs(self) -> None:
        """Create any missing dirs
        """
        if not os.path.exists(self.cache_folder):
            os.makedirs(self.cache_folder)

    def validate(self) -> None:
        """Validate the config object i.e. paths exit
        NOTE: will raise exceptions if issues are encountered.
        FIXME: impl. more validation here
        """
        assert os.path.exists(self.cache_folder)
        self.search_config.validate()
        if self.proxy_config:
            self.proxy_config.validate()
        self.delay_config.validate()
