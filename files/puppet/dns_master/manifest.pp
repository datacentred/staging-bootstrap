# Resource defaults
Exec {
  path => '/bin:/usr/bin:/sbin:/usr/sbin',
}

# Install foreman DNS
class { 'dns':
  forwarders      => [
    '8.8.8.8',
    '8.8.4.4',
  ],
  allow_recursion => [
    '10.20.192.0/24',
  ],
} ->

# Flip the resolver over to the local one
exec { 'sed -i "s/dns-nameservers.*/dns-nameservers 10.20.192.250/" /etc/network/interfaces':
} ->

exec { 'ifdown eth0':
} ->

exec { 'ifup eth0':
}

dns::zone { $::domain:
}

dns::zone { '192.20.10.in-addr.arpa':
  reverse => true,
}
