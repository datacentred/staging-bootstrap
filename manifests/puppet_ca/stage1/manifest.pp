# Vendor packages to install
$packages = [
  'git',
  'puppetserver',
]

# Ruby gems to install
$packages_gem = [
  'hiera-eyaml',
  'deep_merge',
  'toml',
]

# CA source file
$ca_source = '/opt/puppetlabs/puppet/lib/ruby/vendor_ruby/puppet/ssl/certificate_authority.rb'

# Puppet's home directory
$puppet_home = '/opt/puppetlabs/server/data/puppetserver'

# Resource defaults
Exec {
  path => '/bin:/usr/bin:/sbin:/usr/sbin',
}

# Install packages
ensure_packages($packages)

$packages_gem.each |$gem| {

  Package[$packages] ->

  exec { "/opt/puppetlabs/bin/puppetserver gem install ${gem}":
    unless  => "/opt/puppetlabs/server/bin/puppetserver gem list ^${gem}$ | grep ${gem}",
  } ->

  Exec["/opt/puppetlabs/bin/puppet cert generate ${::fqdn}"]

}

# Create the root CA
exec { "/opt/puppetlabs/bin/puppet cert generate ${::fqdn}":
  creates => "/etc/puppetlabs/puppet/ssl/certs/${::fqdn}.pem",
} ->

# Enable wildcards
exec { "sed -i 's/csr\\.subject_alt_names\\.any.*/false/' ${ca_source}":
  onlyif => "grep 'csr\\.subject_alt_names\\.any' ${ca_source}",
} ->

file { '/etc/puppetlabs/puppet/autosign.conf':
  ensure  => file,
  owner   => 'root',
  group   => 'root',
  mode    => '0644',
  content => '*.example.com',
} ->

# Install the eyaml keys
file { '/etc/puppetlabs/puppet/keys':
  ensure => directory,
  owner  => 'puppet',
  group  => 'puppet',
  mode   => '0755',
} ->

file { '/etc/puppetlabs/puppet/keys/public_key.pkcs7.pem':
  ensure => file,
  owner  => 'puppet',
  group  => 'puppet',
  mode   => '0400',
  source => '/tmp/public_key.pkcs7.pem',
} ->

file { '/etc/puppetlabs/puppet/keys/private_key.pkcs7.pem':
  ensure => file,
  owner  => 'puppet',
  group  => 'puppet',
  mode   => '0400',
  source => '/tmp/private_key.pkcs7.pem',
} ->

# Configure SSH
file { "${puppet_home}/.ssh":
  ensure => directory,
  owner  => 'puppet',
  group  => 'puppet',
  mode   => '0755',
} ->

file { "${puppet_home}/.ssh/config":
  ensure  => file,
  owner   => 'puppet',
  group   => 'puppet',
  mode    => '0644',
  content => "Host github.com\nStrictHostKeyChecking no",
} ->

# Install the code
file { '/etc/puppetlabs/code/environments':
  ensure => directory,
  owner  => 'puppet',
  group  => 'puppet',
  mode   => '0775',
} ->

# WARNING: puppet cert generate stealthily creates this which bones git
exec { 'rm -rf /etc/puppetlabs/code/environments/production':
} ->

exec { "git clone https://${deploy_user}:${deploy_pass}@github.com/datacentred/puppet production":
  user    => 'puppet',
  cwd     => '/etc/puppetlabs/code/environments',
  timeout => 3600,
} ->

exec { 'git submodule init':
  user => 'puppet',
  cwd  => '/etc/puppetlabs/code/environments/production',
} ->

exec { 'git submodule update':
  user    => 'puppet',
  cwd     => '/etc/puppetlabs/code/environments/production',
  timeout => 3600,
} ->

file { '/etc/puppetlabs/puppet/hiera.yaml':
  ensure => file,
  owner  => 'root',
  group  => 'root',
  mode   => '0644',
  source => '/tmp/hiera.yaml',
} ->

service { 'puppetserver':
  ensure => running,
  enable => true,
}
