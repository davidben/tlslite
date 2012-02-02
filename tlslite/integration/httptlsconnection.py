# Author: Trevor Perrin
# See the LICENSE file for legal information regarding use of this file.

"""TLS Lite + httplib."""

import socket
import httplib
from tlslite.tlsconnection import TLSConnection
from tlslite.integration.clienthelper import ClientHelper


class HTTPBaseTLSConnection(httplib.HTTPConnection):
    """This abstract class provides a framework for adding TLS support
    to httplib."""

    default_port = 443

    def __init__(self, host, port=None, strict=None):
        if strict == None:
            #Python 2.2 doesn't support strict
            httplib.HTTPConnection.__init__(self, host, port)
        else:
            httplib.HTTPConnection.__init__(self, host, port, strict)

    def connect(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if hasattr(sock, 'settimeout'):
            sock.settimeout(10)
        sock.connect((self.host, self.port))

        #Use a TLSConnection to emulate a socket
        self.sock = TLSConnection(sock)

        #When httplib closes this, close the socket
        self._handshake(self.sock)

    def _handshake(self, tlsConnection):
        """Called to perform some sort of handshake.

        This method must be overridden in a subclass to do some type of
        handshake.  This method will be called after the socket has
        been connected but before any data has been sent.  If this
        method does not raise an exception, the TLS connection will be
        considered valid.

        This method may (or may not) be called every time an HTTP
        request is performed, depending on whether the underlying HTTP
        connection is persistent.

        @type tlsConnection: L{tlslite.TLSConnection.TLSConnection}
        @param tlsConnection: The connection to perform the handshake
        on.
        """
        raise NotImplementedError()


class HTTPTLSConnection(HTTPBaseTLSConnection, ClientHelper):
    """This class extends L{HTTPBaseTLSConnection} to support the
    common types of handshaking."""

    def __init__(self, host, port=None,
                 username=None, password=None,
                 certChain=None, privateKey=None,
                 x509Fingerprint=None,
                 settings = None):
        """Create a new HTTPTLSConnection.

        For client authentication, use one of these argument
        combinations:
         - username, password (SRP)
         - certChain, privateKey (certificate)

        For server authentication, you can either rely on the
        implicit mutual authentication performed by SRP
        or you can do certificate-based server
        authentication with one of these argument combinations:
         - x509Fingerprint

        Certificate-based server authentication is compatible with
        SRP or certificate-based client authentication.

        The constructor does not perform the TLS handshake itself, but
        simply stores these arguments for later.  The handshake is
        performed only when this class needs to connect with the
        server.  Thus you should be prepared to handle TLS-specific
        exceptions when calling methods inherited from
        L{httplib.HTTPConnection} such as request(), connect(), and
        send().  See the client handshake functions in
        L{tlslite.TLSConnection.TLSConnection} for details on which
        exceptions might be raised.

        @type host: str
        @param host: Server to connect to.

        @type port: int
        @param port: Port to connect to.

        @type username: str
        @param username: SRP username.  Requires the
        'password' argument.

        @type password: str
        @param password: SRP password for mutual authentication.
        Requires the 'username' argument.

        @type certChain: L{tlslite.x509certchain.X509CertChain} or
        @param certChain: Certificate chain for client authentication.
        Requires the 'privateKey' argument.  Excludes the SRP arguments.
        
        @type privateKey: L{tlslite.utils.rsakey.RSAKey}
        @param privateKey: Private key for client authentication.
        Requires the 'certChain' argument.  Excludes the SRP arguments.

        @type x509Fingerprint: str
        @param x509Fingerprint: Hex-encoded X.509 fingerprint for
        server authentication.

        @type settings: L{tlslite.handshakesettings.HandshakeSettings}
        @param settings: Various settings which can be used to control
        the ciphersuites, certificate types, and SSL/TLS versions
        offered by the client.
        """

        HTTPBaseTLSConnection.__init__(self, host, port)

        ClientHelper.__init__(self,
                 username, password, 
                 certChain, privateKey,
                 x509Fingerprint,
                 settings)

    def _handshake(self, tlsConnection):
        ClientHelper._handshake(self, tlsConnection)