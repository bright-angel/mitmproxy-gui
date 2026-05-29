import os
import sys
import subprocess


def get_mitmproxy_cert_dir():
    home = os.path.expanduser("~")
    return os.path.join(home, ".mitmproxy")


def get_cert_paths():
    cert_dir = get_mitmproxy_cert_dir()
    return {
        "pem": os.path.join(cert_dir, "mitmproxy-ca-cert.pem"),
        "cer": os.path.join(cert_dir, "mitmproxy-ca-cert.cer"),
        "p12": os.path.join(cert_dir, "mitmproxy-ca-cert.p12"),
    }


def is_cert_generated():
    paths = get_cert_paths()
    return any(os.path.exists(p) for p in paths.values())


def is_cert_installed_windows():
    """Check if mitmproxy CA cert is installed in Windows cert store."""
    try:
        result = subprocess.run(
            ["certutil", "-store", "Root", "mitmproxy"],
            capture_output=True, text=True, timeout=10
        )
        return "mitmproxy" in result.stdout
    except Exception:
        return False


def install_cert_windows():
    paths = get_cert_paths()
    cer_path = paths["cer"]
    if not os.path.exists(cer_path):
        return False, "Certificate file not found. Run mitmproxy once first to generate certs."

    try:
        result = subprocess.run(
            ["certutil", "-addstore", "Root", cer_path],
            capture_output=True, text=True, timeout=15,
            shell=True
        )
        if result.returncode == 0:
            return True, "Certificate installed successfully."
        return False, result.stderr or result.stdout
    except Exception as e:
        return False, str(e)


def is_cert_installed():
    if sys.platform == "win32":
        return is_cert_installed_windows()
    # macOS / Linux — check common paths
    paths = [
        "/etc/ssl/certs/mitmproxy-ca-cert.pem",
        "/usr/local/share/ca-certificates/mitmproxy-ca-cert.crt",
    ]
    for p in paths:
        if os.path.exists(p):
            return True
    # macOS check
    if sys.platform == "darwin":
        try:
            result = subprocess.run(
                ["security", "find-certificate", "-c", "mitmproxy", "/Library/Keychains/System.keychain"],
                capture_output=True, text=True, timeout=10
            )
            return "mitmproxy" in result.stdout.lower()
        except Exception:
            return False
    return False


def install_cert():
    if sys.platform == "win32":
        return install_cert_windows()
    elif sys.platform == "darwin":
        paths = get_cert_paths()
        pem = paths["pem"]
        if not os.path.exists(pem):
            return False, "Certificate file not found."
        try:
            subprocess.run(
                ["sudo", "security", "add-trusted-cert", "-d", "-k",
                 "/Library/Keychains/System.keychain", pem],
                check=True, timeout=15
            )
            return True, "Certificate installed."
        except Exception as e:
            return False, str(e)
    else:
        paths = get_cert_paths()
        pem = paths["pem"]
        if not os.path.exists(pem):
            return False, "Certificate file not found."
        return False, "On Linux, manually copy the cert to your CA trust store."
