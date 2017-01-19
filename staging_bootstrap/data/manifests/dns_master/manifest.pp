# Resource defaults
Exec {
  path => '/bin:/usr/bin:/sbin:/usr/sbin',
}

$packages = [
  'dnsutils', # nsupdate
]

ensure_packages($packages)

# Install foreman DNS
class { 'dns':
  forwarders      => [
    '8.8.8.8',
    '8.8.4.4',
  ],
  allow_recursion => [
    '10.25.192.0/24',
  ],
} ->

# Flip the resolver over to the local one
exec { 'sed -i "s/dns-nameservers.*/dns-nameservers 10.25.192.250 10.25.192.251/" /etc/network/interfaces':
  unless => 'grep "dns-nameservers 10.25.192.250 10.25.192.251" /etc/network/interfaces',
} ~>

exec { 'ifdown ens3':
  refreshonly => true,
} ~>

exec { 'ifup ens3':
  refreshonly => true,
}

dns::zone { $::domain:
}

dns::zone { '192.25.10.in-addr.arpa':
  reverse => true,
}
