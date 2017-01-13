# Enable non SSL operation and restart the server

File {
  ensure => file,
  owner  => 'root',
  group  => 'root',
  mode   => '0644',
}

# Install the required Non-SSL configuration
file { '/etc/puppetlabs/puppetserver/conf.d/webserver.conf':
  source => '/tmp/webserver.conf',
}

file { '/etc/puppetlabs/puppetserver/conf.d/puppetserver.conf':
  source => '/tmp/puppetserver.conf',
}

file { '/etc/puppetlabs/puppetserver/conf.d/auth.conf':
  source => '/tmp/auth.conf',
}

# Restart the webserver
File <||> ~>

service { 'puppetserver':
  ensure => running,
}
