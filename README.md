# DataCentred Staging Environment Bootstrapper

## Description

Automates the process of bootstrapping a virtualized staging environment from establishment
of an authoritative name service for the domain, through to a functioning Foreman installation
for further provisioning of virtual machines.

## Building

    apt-get -y install python-setuptools gcc make libffi-dev
    gem install fpm
    fpm -s python -t deb \
      --depends python-paramiko \
      --depends python-pkg-resources \
      --deb-default etc/default/staging-bootstrap .

## Configuring

Open the configuration file:

    vim /etc/default/staging-boostrap

Fill in the blanks.  The _github_ section takes a username and password which has read only
access to a git repository containing puppet code.  The _eyaml_ section contains paths to
PKCS7 keys used to decrypt hiera YAML data.

## Details

Allows the subnet and domain to be configured before creating a DNS name server with virt-install.
Installation is via the Ubuntu network installer, preseeds and finish scripts (to configure
network configuration etc.) are served by a simple HTTP server listening on the gateway address
of the specified subnet.  The DNS server is configured with a zone for the specified domain and
the reverse zone for the subnet, RNDC is also configured so that DNS resource records can be
added during the bootsrapping process.

A Puppet CA is then created to allow the generation of certificates.  The CA initially listens
on an SSL socket served via Apache.  A number of source code modification are performed in
order to allow auto-signing of certificate requests containing alternative names and wildcards
which are interactive/disabled by default respectively.

A HA Proxy gateway VM is then created which exposes the PuppetCA port on both an internal and
external VIP.  The X.509 certificate is signed with alternative name wildcards for both
internal and external domains.  An A record is added for the puppet service pointing to the
internal VIP, then the puppet CA is reconfigured as an unencrypted service with all subsequent
requests going via the gateway which performs SSL termination.
