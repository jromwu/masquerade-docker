# masquerade-docker
A docker compose application to generate and capture traffic proxied or unproxied. Aiming to generate QUIC traffic and capture MASQUE traffic (using implementation of [masquerade](https://github.com/jromwu/masquerade/)). 

Topology:
```
                                          Capture here                           Capture here  
Client <------> Webdriver (Chrome or Firefox) <--> Gateway <--------> Proxy (client) <--> Capturer <--> Proxy-server <--> Internet
  Selenium remote test                                     <-SOCKS5->                <-----MASQUE----->           
```

## Prerequisite
Linux kernel must enable `TPROXY` module for `iptables` in order for gateway to proxy UDP traffic. 

Right now x86 docker images are being used for Selenium. One can switch to Seleniarm's images for arm processer.

## To-Do
- [ ] Write application for Selenium Webdriver
 - [ ] Google Hangout chat
 - [ ] Google Hangout call
 - [ ] Google Meet meeting
 - [ ] Youtube video streaming
 - [ ] Google Play music streaming
 - [ ] Google Drive file download
- [x] Set up masquerade server for proxy
- [x] Add Selenium Webdriver
- [ ] Compile curl with QUIC in client
