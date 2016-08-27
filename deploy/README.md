Deployment is done with Ansible
You will need to install Ansible.
TODO: how?

You will need to add an `inventory.ini` file inside this directory.
It will look something like

```
[production]
104.x.x.x

[development]
locahost
```

then, from the project root directory.

To install:
```
ansible-playbook -i deploy/inventory.ini deploy/playbooks/production.yml --user bryan -e@"deploy/server-vars.yml" -t install
```

* Change `production.yml` to whichever of `production|development` server you want to deploy to.
* `-e@deploy/server-vars.yml` will include an additional vars file which you should create and should store your secrets, like API keys
* If you have not set up the host and your ssh config to use an ssh key, you will need to add the `--ask-pass` argument to these)

To deploy (update software from repositories, restart servers):
```
ansible-playbook -i deploy/inventory.ini deploy/playbooks/production.yml --user bryan -e@"deploy/server-vars.yml" -t deploy
```

* as it is, you will have to manually add a `twitterauth.json` file similar to this

```
{
    "consumer_key": "xxxxxxxxx",
    "consumer_secret": "xxxxxxxxx",
    "access_token_key": "   xxxxxxxxx",
    "access_token_secret": "xxxxxxxxx"
}
```

and then change the value `TWITTER_AUTH_FILE_PATH` in the `settings.cfg` file to point to that file.

* You will also need to point the value for `STATES_SHAPE_FILE_PATH` file in `settings.cfg` to your states file path. TODO:  can probably make that generic

