# coding: utf-8
import hashlib
import sys

import pytest

from nxdrive.manager import ProxySettings
from nxdrive.utils import guess_digest_algorithm, guess_mime_type, \
    guess_server_url, is_generated_tmp_file


def test_proxy_settings():
    proxy = ProxySettings()
    proxy.from_url('localhost:3128')
    assert not proxy.username
    assert not proxy.password
    assert not proxy.authenticated
    assert proxy.server == 'localhost'
    assert proxy.port == 3128
    assert not proxy.proxy_type
    assert proxy.to_url() == 'localhost:3128'
    assert proxy.to_url(False) == 'localhost:3128'
    
    proxy.from_url('user@localhost:3128')
    assert proxy.username == 'user'
    assert not proxy.password
    assert not proxy.authenticated
    assert proxy.server == 'localhost'
    assert proxy.port == 3128
    assert not proxy.proxy_type
    assert proxy.to_url() == 'localhost:3128'
    assert proxy.to_url(False) == 'localhost:3128'
    
    proxy.from_url('user:password@localhost:3128')
    assert proxy.username == 'user'
    assert proxy.password == 'password'
    assert proxy.authenticated
    assert proxy.server == 'localhost'
    assert proxy.port == 3128
    assert not proxy.proxy_type
    assert proxy.to_url() == 'user:password@localhost:3128'
    assert proxy.to_url(False) == 'localhost:3128'
    
    proxy.from_url('http://user:password@localhost:3128')
    assert proxy.username == 'user'
    assert proxy.password == 'password'
    assert proxy.authenticated
    assert proxy.server == 'localhost'
    assert proxy.port == 3128
    assert proxy.proxy_type == 'http'
    assert proxy.to_url() == 'http://user:password@localhost:3128'
    assert proxy.to_url(False) == 'http://localhost:3128'
    
    proxy.from_url('https://user:password@localhost:3129')
    assert proxy.username == 'user'
    assert proxy.password == 'password'
    assert proxy.authenticated
    assert proxy.server == 'localhost'
    assert proxy.port == 3129
    assert proxy.proxy_type == 'https'
    assert proxy.to_url() == 'https://user:password@localhost:3129'
    assert proxy.to_url(False) == 'https://localhost:3129'


def test_generated_tempory_file():
    # Normal
    assert is_generated_tmp_file('README') == (False, None)

    # Any temporary file
    assert is_generated_tmp_file('Book1.bak') == (True, False)
    assert is_generated_tmp_file('pptED23.tmp') == (True, False)
    assert is_generated_tmp_file('9ABCDEF0.tep') == (False, None)

    # AutoCAD
    assert is_generated_tmp_file('atmp9716') == (True, False)
    assert is_generated_tmp_file('7151_CART.dwl') == (True, False)
    assert is_generated_tmp_file('7151_CART.dwl2') == (True, False)
    assert is_generated_tmp_file('7151_CART.dwg') == (False, None)

    # Microsoft Office
    assert is_generated_tmp_file('A239FDCA') == (True, True)
    assert is_generated_tmp_file('A2Z9FDCA') == (False, None)
    assert is_generated_tmp_file('A239FDZA') == (False, None)
    assert is_generated_tmp_file('A2D9FDCA1') == (False, None)
    assert is_generated_tmp_file('~A2D9FDCA1.tm') == (False, None)


def test_guess_mime_type():
    # Text
    assert guess_mime_type('text.txt') == 'text/plain'
    assert guess_mime_type('text.html') == 'text/html'
    assert guess_mime_type('text.css') == 'text/css'
    assert guess_mime_type('text.csv') == 'text/csv'
    assert guess_mime_type('text.js') == 'application/javascript'

    # Image
    assert guess_mime_type('picture.jpg') == 'image/jpeg'
    assert guess_mime_type('picture.png') == 'image/png'
    assert guess_mime_type('picture.gif') == 'image/gif'
    assert guess_mime_type('picture.bmp') in ('image/x-ms-bmp', 'image/bmp')
    assert guess_mime_type('picture.tiff') == 'image/tiff'
    assert guess_mime_type('picture.ico') in ('image/x-icon', 'image/vnd.microsoft.icon')

    # Audio
    assert guess_mime_type('sound.mp3') == 'audio/mpeg'
    assert guess_mime_type('sound.wma') in ('audio/x-ms-wma', 'application/octet-stream')
    assert guess_mime_type('sound.wav') in ('audio/x-wav', 'audio/wav')

    # Video
    assert guess_mime_type('video.mpeg') == 'video/mpeg'
    assert guess_mime_type('video.mp4') == 'video/mp4'
    assert guess_mime_type('video.mov') == 'video/quicktime'
    assert guess_mime_type('video.wmv') in ('video/x-ms-wmv', 'application/octet-stream')
    assert guess_mime_type('video.avi') in ('video/x-msvideo', 'video/avi')

    # Office
    assert guess_mime_type('office.doc') == 'application/msword'
    assert guess_mime_type('office.xls') == 'application/vnd.ms-excel'
    assert guess_mime_type('office.ppt') == 'application/vnd.ms-powerpoint'

    # PDF
    assert guess_mime_type('document.pdf') == 'application/pdf'

    # Unknown
    assert guess_mime_type('file.unknown') == 'application/octet-stream'

    # Cases badly handled by Windows
    # See https://jira.nuxeo.com/browse/NXP-11660
    # and http://bugs.python.org/issue15207
    if sys.platform == 'win32':
        # Text
        assert guess_mime_type('text.xml') == 'text/xml'

        # Image
        assert guess_mime_type('picture.svg') in ('image/svg+xml',
                                                  'application/octet-stream')

        # Video
        assert guess_mime_type('video.flv') == 'application/octet-stream'

        # Office
        assert guess_mime_type('office.docx') in ('application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                                                  'application/octet-stream')
        assert guess_mime_type('office.xlsx') in ('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                                                  'application/octet-stream')
        assert guess_mime_type('office.pptx') in ('application/vnd.openxmlformats-officedocument.presentationml.presentation',
                                                  'application/x-mspowerpoint.12',
                                                  'application/octet-stream')

        assert guess_mime_type('office.odt') in ('application/vnd.oasis.opendocument.text',
                                                 'application/octet-stream')
        assert guess_mime_type('office.ods') in ('application/vnd.oasis.opendocument.spreadsheet',
                                                 'application/octet-stream')
        assert guess_mime_type('office.odp') in ('application/vnd.oasis.opendocument.presentation',
                                                 'application/octet-stream')
    else:
        # Text
        assert guess_mime_type('text.xml') == 'application/xml'

        # Image
        assert guess_mime_type('picture.svg') == 'image/svg+xml'

        # Video
        assert guess_mime_type('video.flv') == 'video/x-flv'

        # Office
        assert guess_mime_type('office.docx') == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        assert guess_mime_type('office.xlsx') == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        assert guess_mime_type('office.pptx') == 'application/vnd.openxmlformats-officedocument.presentationml.presentation'

        assert guess_mime_type('office.odt') == 'application/vnd.oasis.opendocument.text'
        assert guess_mime_type('office.ods') == 'application/vnd.oasis.opendocument.spreadsheet'
        assert guess_mime_type('office.odp') == 'application/vnd.oasis.opendocument.presentation'


def test_guess_digest_algorithm():
    md5_digest = hashlib.md5('joe').hexdigest()
    assert guess_digest_algorithm(md5_digest) == 'md5'
    sha1_digest = hashlib.sha1('joe').hexdigest()
    assert guess_digest_algorithm(sha1_digest) == 'sha1'

    # For now only MD5 and SHA1 are supported
    sha256_digest = hashlib.sha256('joe').hexdigest()
    with pytest.raises(ValueError):
        guess_digest_algorithm(sha256_digest)


def test_guess_server_url():
    domain = 'localhost'
    good_url = 'http://localhost:8080/nuxeo'
    assert guess_server_url(domain) == good_url

    # HTTPS domain
    domain = 'intranet.nuxeo.com'
    good_url = 'https://intranet.nuxeo.com/nuxeo'
    assert guess_server_url(domain) == good_url

    # With additional parameters
    domain = 'https://intranet.nuxeo.com/nuxeo?TenantId=0xdeadbeaf'
    good_url = domain
    assert guess_server_url(domain) == good_url

    # Incomplete URL
    domain = 'https://intranet.nuxeo.com'
    good_url = 'https://intranet.nuxeo.com/nuxeo'
    assert guess_server_url(domain) == good_url

    # Bad IP
    domain = '1.2.3.4'
    good_url = None
    assert guess_server_url(domain) == good_url

    # Bad protocal
    domain = 'htto://intranet.nuxeo.com/nuxeo'
    good_url = None
    assert guess_server_url(domain) == good_url
