from typing import Optional

METADATA =\
{
	'name': 'App',
	'description': 'App platform',
	'version': '1.0.0',
	'license': 'OpenRAIL-AS',
	'author': 'Dev',
	'url': 'https://example.com'
}


def get(key : str) -> Optional[str]:
	return METADATA.get(key)
