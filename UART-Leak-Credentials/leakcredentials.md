During local testing we observed that device secrets (including the web admin account admin and its password, as well as configured Wi-Fi SSID/password) are printed to the serial console (UART) in cleartext. The credentials are present both in /system/www/system.ini and /system/param/login.cgi, and identical credentials are visible on the UART during boot/runtime without authentication.

As show in the following video Wireless and Admin credentials are leaked:

[UARTLeakGIF](bootUART.gif)
[UARTLeak](bootUART.mp4)

Impact: An attacker with physical access to the device (or to accessible UART pads) can obtain administrative and wireless credentials and gain administrative access to the device and/or join the local network. This enables device takeover, configuration changes, firmware replacement, data exfiltration, and network pivoting.

Recommendation: Remove printing of secrets to UART, redact/mask secrets in logs, disable UART by default in production builds or gate it behind a hardware jumper, and eliminate hardcoded/shared credentials by provisioning unique per-device credentials or secure onboarding. Implement encrypted storage for credentials and consider secure boot to prevent firmware tampering.
