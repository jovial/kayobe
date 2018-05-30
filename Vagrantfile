# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure('2') do |config|

  config.vm.provider :libvirt do |domain|
    config.vm.synced_folder './', '/vagrant', type: 'nfs', nfs_version: "3", "nfs_udp": false
  end

  config.vm.define "mitmproxy" do |mitmproxy|
    mitmproxy.vm.hostname = 'mitmproxy'

    mitmproxy.vm.network 'private_network', ip: '192.168.33.5',
                         libvirt__forward_mode: 'none'

    mitmproxy.vm.box = 'centos/7'

    mitmproxy.vm.provider :libvirt do |domain|
      domain.uri = 'qemu+unix:///system'
      domain.driver = 'kvm'
      domain.memory = 4096
      domain.cpus = 4
      domain.nested = true
      domain.cpu_mode = 'host-model'
    end

    mitmproxy.vm.provision "ansible" do |ansible|
      ansible.playbook = "provisioning/provision-mitmproxy.yml"
      #ansible.verbose = "-vvvv"
    end

  end


  config.vm.define "default" do |default|

  default.vm.hostname = 'controller1'

  default.vm.network 'private_network', ip: '192.168.33.3',
                     libvirt__forward_mode: 'none'

  default.vm.box = 'centos/7'

  default.vm.provider 'virtualbox' do |vb|
    vb.memory = '4096'
    vb.linked_clone = true
    vb.cpus = "4"
  end

  default.vm.provider 'vmware_fusion' do |vmware|
    vmware.vmx['memsize'] = '4096'
    vmware.vmx['vhv.enable'] = 'TRUE'
    vmware.linked_clone = true
  end

  default.vm.provider :libvirt do |domain|
    domain.uri = 'qemu+unix:///system'
    domain.driver = 'kvm'
    domain.memory = 8192
    domain.cpus = 4
    domain.nested = true
    domain.cpu_mode = 'host-model'
    #default.vm.synced_folder './', '/vagrant', type: 'nfs', nfs_version: "3", "nfs_udp": false
  end

  default.vm.provision 'shell', inline: <<-SHELL
    echo "cat > /etc/selinux/config << EOF
SELINUX=disabled
SELINUXTYPE=targeted
EOF" | sudo -s
      cat /etc/selinux/config
  SHELL

  # NOTE: Reboot to apply selinux change, requires the reload plugin:
  #   vagrant plugin install vagrant-reload
  default.vm.provision :reload

  default.vm.provision "shell", inline: <<-SHELL
    sudo yum group install "Development Tools" -y
  SHELL

  default.vm.provision "ansible" do |ansible|
    ansible.playbook = "provisioning/provision-kayobe.yml"
    #ansible.verbose = "-vvvv"
  end


  default.vm.provision 'shell', privileged: false, inline: <<-SHELL
#    cat << EOF | sudo tee /etc/sysconfig/network-scripts/ifcfg-eth1
#DEVICE=eth1
#USERCTL=no
#BOOTPROTO=none
#IPADDR=192.168.121.3
#NETMASK=255.255.255.0
#ONBOOT=yes
#NM_CONTROLLED=no
#EOF
#    sudo ifup eth1
    # PIP Doesn't use system wide trsuted certificates
    export PIP_CERT=/etc/pki/ca-trust/source/anchors/mitmproxy.pem
    /vagrant/dev/install.sh

    # Configure the legacy development environment. This has been retained
    # while transitioning to the new development environment.
    cat > /vagrant/kayobe-env << EOF
export KAYOBE_CONFIG_PATH=/vagrant/etc/kayobe
export KOLLA_CONFIG_PATH=/vagrant/etc/kolla
EOF
    cp /vagrant/dev/dev-vagrant.yml /vagrant/etc/kayobe/
    cp /vagrant/dev/dev-hosts /vagrant/etc/kayobe/inventory
    cp /vagrant/dev/dev-vagrant-network-allocation.yml /vagrant/etc/kayobe/network-allocation.yml
  SHELL
  end
end
