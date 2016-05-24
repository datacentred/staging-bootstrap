# Vendor packages to install
$packages = [
  'git',
  'puppetmaster-common',
]

# Ruby gems to install
$packages_gem = [
  'hiera-eyaml',
  'deep_merge',
]

$gem_defaults = {
  'provider' => 'gem',
}

# CA source file
$ca_source = '/usr/lib/ruby/vendor_ruby/puppet/ssl/certificate_authority.rb'

# Resource defaults
Exec {
  path => '/bin:/usr/bin:/sbin:/usr/sbin',
}

# Required apache modules
include ::apache
include ::apache::mod::ssl
include ::apache::mod::headers
include ::apache::mod::passenger

ensure_packages($packages)
ensure_packages($packages_gem, $gem_defaults)

# Install packages
Package[$packages] ->

Package[$packages_gem] ->

# Create the root CA
exec { "puppet cert generate ${::fqdn}":
  creates => "/var/lib/puppet/ssl/certs/${::fqdn}.pem",
} ->

# Apply CA source hacks before apache starts
exec { "sed -i 's/unless allow_dns_alt_names/unless true/' ${ca_source}":
  onlyif => "grep 'unless allow_dns_alt_names' ${ca_source}",
} ->

exec { "sed -i 's/csr\\.subject_alt_names\\.any.*/false/' ${ca_source}":
  onlyif => "grep 'csr\\.subject_alt_names\\.any' ${ca_source}",
} ->

# Create the rack/passenger configuration
file { '/etc/puppet/rack/':
  ensure => directory,
  owner  => 'root',
  group  => 'root',
  mode   => '0755',
} ->

file { '/etc/puppet/rack/tmp':
  ensure => directory,
  owner  => 'root',
  group  => 'root',
  mode   => '0755',
} ->

file { '/etc/puppet/rack/public':
  ensure => directory,
  owner  => 'root',
  group  => 'root',
  mode   => '0755',
} ->

file { '/etc/puppet/rack/config.ru':
  ensure => file,
  owner  => 'puppet',
  group  => 'puppet',
  mode   => '0644',
  source => '/usr/share/puppet/ext/rack/config.ru',
} ->

file { '/etc/puppet/autosign.conf':
  ensure  => file,
  owner   => 'root',
  group   => 'root',
  mode    => '0644',
  content => '*.example.com',
} ->

# Install the eyaml keys
file { '/etc/puppet/keys':
  ensure => directory,
  owner  => 'puppet',
  group  => 'puppet',
  mode   => '0755',
} ->

file { '/etc/puppet/keys/private_key.pkcs7.pem':
  ensure => file,
  owner  => 'puppet',
  group  => 'puppet',
  mode   => '0400',
  source => '/tmp/private_key.pkcs7.pem',
} ->

# Configure SSH
file { '/var/lib/puppet/.ssh':
  ensure => directory,
  owner  => 'puppet',
  group  => 'puppet',
  mode   => '0755',
} ->

file { '/var/lib/puppet/.ssh/config':
  ensure  => file,
  owner   => 'puppet',
  group   => 'puppet',
  mode    => '0644',
  content => "Host github.com\nStrictHostKeyChecking no",
} ->

# Install the code
file { '/etc/puppet/environments':
  ensure => directory,
  owner  => 'puppet',
  group  => 'puppet',
  mode   => '0775',
} ->

# WARNING: puppet cert generate stealthily creates this which bones git
exec { 'rmdir /etc/puppet/environments/production':
} ->

exec { "git clone https://${deploy_user}:${deploy_pass}@github.com/datacentred/puppet production":
  user    => 'puppet',
  cwd     => '/etc/puppet/environments',
  timeout => 3600,
} ->

exec { 'git submodule init':
  user => 'puppet',
  cwd  => '/etc/puppet/environments/production',
} ->

exec { 'git submodule update':
  user    => 'puppet',
  cwd     => '/etc/puppet/environments/production',
  timeout => 3600,
} ->

file { '/etc/puppet/hiera.yaml':
  ensure => file,
  owner  => 'root',
  group  => 'root',
  mode   => '0644',
  source => '/tmp/hiera.yaml',
} ->

Class['::apache']

apache::vhost { $::fqdn:
  port              => 8140,
  ssl               => true,
  ssl_cipher        => 'HIGH:!aNull:!MD5',
  ssl_cert          => "/var/lib/puppet/ssl/certs/${::fqdn}.pem",
  ssl_key           => "/var/lib/puppet/ssl/private_keys/${::fqdn}.pem",
  ssl_chain         => '/var/lib/puppet/ssl/certs/ca.pem',
  ssl_ca            => '/var/lib/puppet/ssl/certs/ca.pem',
  ssl_crl           => '/var/lib/puppet/ssl/crl.pem',
  ssl_crl_check     => 'chain',
  ssl_verify_client => 'optional',
  ssl_verify_depth  => 1,
  ssl_options       => '+StdEnvVars +ExportCertData',
  request_headers   => [
    'unset X-Forwarded-For',
    'set X-SSL-Subject %{SSL_CLIENT_S_DN}e',
    'set X-Client-DN %{SSL_CLIENT_S_DN}e',
    'set X-Client-Verify %{SSL_CLIENT_VERIFY}e',
  ],
  docroot           => '/etc/puppet/rack/public/',
  manage_docroot    => false,
  rack_base_uris    => [
    '/',
  ],
  directories       => {
    'path'    => '/etc/puppet/rack/',
    'options' => 'none',
  },
}
