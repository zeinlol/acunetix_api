import json
from datetime import datetime
from enum import Enum
from typing import NoReturn

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.firefox.options import Options


class Severity(Enum):
    high = 3
    medium = 2
    low = 1
    informational = 0


def timed_print(string: str) -> NoReturn:
    print(f'{datetime.now()}: {string}')


def get_page(file_absolute_path: str):
    options = Options()
    options.headless = True
    driver = webdriver.Firefox(options=options, executable_path='geckodriver')
    driver.get(url=f'file://{file_absolute_path}')
    generated_html = driver.page_source
    driver.quit()
    return generated_html


def get_scan_details(store: dict, soup: BeautifulSoup):
    table = soup.find('table', class_='panel-table')
    table2 = soup.find('table', class_='panel-table-2')

    store['audit_result']['scan_metrics'].update({
        'target': table.find('a', {'data-innertext': 'target_url'}).get('href'),
        'duration': table.find('td', {'data-innertext': 'duration'}).text,
        'total_requests': table.find('td', {'data-innertext': 'total_requests'}).text,
        'avg_response_time': table.find('td', {'data-innertext': 'avg_response_time'}).text,
        'max_response_time': table.find('td', {'data-innertext': 'max_response_time'}).text,
        'vuln_instances_total': table2.find('td', {'data-innertext': 'vuln_instances_total'}).text
    })
    return store


def get_vuln_entries(soup: BeautifulSoup):
    vuln_entries = []
    items = soup.find_all('tr', {'class': 'impact_entry', 'data-subsection': 'vulnerability'})
    for item in items:
        severity = item.find('td', class_='severity').find('span', {'style': ''}).find('label').text
        vuln_entry = {
            'severity': Severity[severity.lower()].value,
            'name': item.find('strong', {'data-innertext': 'name'}).text
        }
        vuln_entries.append(vuln_entry)
    return vuln_entries


def get_vuln_urls(soup: BeautifulSoup):
    vuln_urls = []
    vulns = soup.find('div', class_='vuln_urls').find_all('div', class_='vulnerability')
    for vuln in vulns:
        url = vuln.find('div', class_='url').find('div', {'data-innertext': 'url'}).text
        details = vuln.find('div', class_='details').text
        request = vuln.find('div', {'class': 'tab_content', 'data-tab-content': 'request'}).find('pre').text
        response = vuln.find('div', {'class': 'tab_content', 'data-tab-content': 'response'}).find('pre').text
        vuln_url = {
            'url': url,
            'description': details,
            'evidence': [{
                'url': url,
                'request': request,
                'response': response
            }]
        }
        vuln_urls.append(vuln_url)
    return vuln_urls


def get_vuln_instances(store: dict, soup: BeautifulSoup):
    issues = []
    vuln_entries = get_vuln_entries(soup=soup)
    vuln_entries_details = soup.find('div', {'id': 'section_vuln_details'}).find_all('div', class_='vuln_type')
    for vuln_entry, vuln_entry_details in zip(vuln_entries, vuln_entries_details):
        vuln_urls = get_vuln_urls(soup=vuln_entry_details)
        for vuln_url in vuln_urls:
            vuln_entry.update(vuln_url)
            issues.append(vuln_entry)
    store['audit_result'].update({'issues': issues})
    return store


def get_vuln_stats(store, soup):
    levels = ['high_count', 'medium_count', 'low_count', 'info_count']
    stats = soup.find('div', {
        'class': 'row center-xs middle-xs',
        'data-template': 'stat_severity_counts'
    }).find_all('span')
    for stat, level in zip(stats, levels):
        store['audit_result']['stats'].update({f'{level}': stat.text})
    return store


def parse(file_absolute_path: str):
    store = {'audit_result': {
        'scan_metrics': {},
        'issues': [],
        'stats': {}
    }}
    generated_html = get_page(file_absolute_path=file_absolute_path)
    timed_print('The generated report page was successfully received.')
    soup = BeautifulSoup(generated_html, 'lxml')
    store = get_scan_details(store=store, soup=soup)
    timed_print('Parsing of general report data is complete.')
    store = get_vuln_instances(store=store, soup=soup)
    store = get_vuln_stats(store=store, soup=soup)
    timed_print('Completed parsing of vulnerability data from the report.')
    with open('output.json', 'w') as f:
        json.dump(store, f, indent=4)
