# Required apache modules
include ::apache
include ::apache::mod::passenger

apache::vhost { $::fqdn:
  port              => 8140,
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
