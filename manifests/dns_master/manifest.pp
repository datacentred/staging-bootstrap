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
exec { 'sed -i "s/dns-nameservers.*/dns-nameservers 10.25.192.250/" /etc/network/interfaces':
} ->

exec { 'ifdown ens3':
} ->

exec { 'ifup ens3':
}

dns::zone { $::domain:
}

dns::zone { '192.25.10.in-addr.arpa':
  reverse => true,
}
