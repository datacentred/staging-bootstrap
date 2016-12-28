include ::haproxy
include ::keepalived

# Create the key/cert pair for haproxy
concat { '/etc/ssl/private/puppet.crt':
  ensure => present,
  owner  => 'haproxy',
  group  => 'haproxy',
  mode   => '0440',
}

concat::fragment { 'haproxy puppet key':
  target => '/etc/ssl/private/puppet.crt',
  source => "/etc/puppetlabs/puppet/ssl/private_keys/${::fqdn}.pem",
  order  => '1',
}

concat::fragment { 'haproxy puppet cert':
  target => '/etc/ssl/private/puppet.crt',
  source => "/etc/puppetlabs/puppet/ssl/certs/${::fqdn}.pem",
  order  => '2',
} 

# Ensure haproxy 1.5 (with SSL) is installed from backports
apt::pin { 'trusty-backports':
  priority => 700,
} ->

# Install the package/user
Package['haproxy'] ->

# Before the certificate with the correct permissions
Concat['/etc/ssl/private/puppet.crt'] ->

# Bootstrap the puppet listener service
haproxy::frontend { 'puppet':
  mode    => 'http',
  bind    => {
    ':8140' => [
      'ssl',
      'no-sslv3',
      'ciphers ECDH+AESGCM:DH+AESGCM:ECDH+AES256:DH+AES256:ECDH+AES128:DH+AES:ECDH+3DES:DH+3DES:RSA+AESGCM:RSA+AES:RSA+3DES:!aNULL:!MD5:!DSS',
      'crt /etc/ssl/private/puppet.crt',
      'ca-file /etc/puppetlabs/puppet/ssl/certs/ca.pem',
      'verify optional',
    ],
  },
  options => {
    'option'          => 'http-server-close',
    'default_backend' => 'puppet',
    'use_backend'     => [
      'puppetca if { path -m sub certificate }',
    ],
    'http-request'    => [
      'set-header X-SSL-Subject %{+Q}[ssl_c_s_dn]',
      'set-header X-Client-DN %{+Q}[ssl_c_s_dn]',
      'set-header X-Client-Verify SUCCESS if { ssl_c_verify 0 }',
      'set-header X-Client-Verify NONE unless { ssl_c_verify 0 }',
    ],
  },
}

haproxy::backend { 'puppetca':
  collect_exported => false,
  options          => {
    mode => 'http',
  },
}

haproxy::balancermember { 'puppetca':
  listening_service => 'puppetca',
  ports             => '8140',
  server_names      => [
    'puppetca.example.com',
  ],
  ipaddresses       => [
    '10.25.192.3',
  ],
  options           => 'check',
}

haproxy::backend { 'puppet':
  collect_exported => false,
  options          => {
    mode => 'http',
  },
}

haproxy::balancermember { 'puppet':
  listening_service => 'puppet',
  ports             => '8140',
  server_names      => [
    'puppetca.example.com',
  ],
  ipaddresses       => [
    '10.25.192.3',
  ],
  options           => 'check',
}

haproxy::listen { 'puppetdb':
  collect_exported => false,
  mode             => 'http',
  bind             => {
    ':8081' => [
      'ssl',
      'no-sslv3',
      'ciphers ECDH+AESGCM:DH+AESGCM:ECDH+AES256:DH+AES256:ECDH+AES128:DH+AES:ECDH+3DES:DH+3DES:RSA+AESGCM:RSA+AES:RSA+3DES:!aNULL:!MD5:!DSS',
      'crt /etc/ssl/private/puppet.crt',
      'crl-file /etc/puppetlabs/puppet/ssl/crl.pem',
      'ca-file /etc/puppetlabs/puppet/ssl/certs/ca.pem',
      'verify required',
    ],
  },
  options          => {
  },
}

haproxy::balancermember { 'puppetdb':
  listening_service => 'puppetdb',
  ports             => '8081',
  server_names      => [
    'puppetdb0.example.com',
  ],
  ipaddresses       => [
    '10.25.192.9',
  ],
  options           => 'ssl ca-file /etc/puppetlabs/puppet/ssl/certs/ca.pem crt /etc/ssl/private/puppet.crt check check-ssl',
}

keepalived::vrrp::instance { 'VI_1':
  interface         => 'ens3',
  state             => 'SLAVE',
  virtual_router_id => '1',
  priority          => '100',
  virtual_ipaddress => '10.25.192.2/24',
}

keepalived::vrrp::instance { 'VI_2':
  interface         => 'ens4',
  state             => 'SLAVE',
  virtual_router_id => '2',
  priority          => '100',
  virtual_ipaddress => '185.43.217.138/29',
}
