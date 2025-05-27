## Creating a Plugin

In this guide we will dive into how to create a Climweb plugin, discuss the plugin architecture and give an example
plugin to get inspiration from and discuss how to publish your plugin.

### Plugin Architecture

A ClimWeb Plugin is fundamentally a folder named after the plugin. The folder should be
a [Django/Wagtail App](https://docs.djangoproject.com/en/5.1/ref/applications/)

#### Initialize your plugin from the plugin template

The plugin template is a [cookiecutter](https://cookiecutter.readthedocs.io/en/stable/installation.html) template that
generates a plugin with the required structure and files. This ensures that the plugin follows the expected structure
and can be easily installed into climweb.

To instantiate the template, execute the following commands from the directory where you want to create the plugin:

```sh
pip install cookiecutter
cookiecutter gh:wmo-raf/climweb --directory plugin-boilerplate
```

For more details on using the plugin boilerplate, you can follow the [step-by-step guide](#plugin-boilerplate) on
creating a plugin using the plugin boilerplate.

#### Plugin Installation API

A Climweb docker image contains the following bash scripts that are used to install plugins. They can be used
to install a plugin into an existing adl container at runtime. `install_plugin.sh` can be used to install a
plugin from an url, a git repo or a local folder on the filesystem.

You can find these scripts in the following locations in the built images:

1. `/deploy/plugins/install_plugin.sh`

On this repo, you can find the scripts in the `deploy/plugins` folder.

These scripts expect a ClimWeb plugin to follow the conventions described below:

#### Plugin File Structure

The `install_plugin.sh` script expect your plugin to have a specific structure as follows:

```
├── plugin_name
│  ├── climweb_plugin_info.json (A simple json file containing info about your plugin)
|  ├── setup.py
|  ├── build.sh (Called when installing the plugin in a Dockerfile/container)
|  ├── runtime_setup.sh (Called on first runtime startup of the plugin)
|  ├── uninstall.sh (Called when uninstalling the plugin in a container)
|  ├── src/plugin_name/src/config/settings/settings.py (Optional Django setting file)
```

The folder contains three bash files which will be automatically called by climweb's plugin scripts during
installation and uninstallation of the plugin. You can use these scripts to perform extra build steps, installation of
packages and other docker container build steps required by your plugin.

1. `build.sh`: Called on container startup if a runtime installation is occurring.
2. `runtime_setup.sh`: Called the first time a container starts up after the plugin has been installed, useful for
   running superuser commands on the container.
3. `uninstall.sh`: Called on uninstall, the database will be available and so any backwards migrations should be run
   here.

#### The plugin info file

The `climweb_plugin_info.json` file is a json file, in your root plugin folder, containing metadata about your
plugin. It should have the following JSON structure:

```json
{
  "name": "TODO",
  "version": "TODO",
  "description": "TODO",
  "author": "TODO",
  "author_url": "TODO",
  "url": "TODO",
  "license": "TODO",
  "contact": "TODO"
}
```

#### Expected plugin structure when installing from a git repository

When installing a plugin from git, the repo should contain a single plugins folder, inside which there should a single
plugin folder following the structure above and has the same name as your plugin.

By default, the `plugin boilerplate` generates a repository with this structure.

For example a conforming git repo should contain something like:

```
├─ * (an outermost wrapper directory named anything is allowed but not required) 
│  ├── plugins/ 
│  │  ├── plugin_name
│  |  |  ├── climweb_plugin_info.json
|  |  |  ├── setup.py
|  |  |  ├── build.sh
|  |  |  ├── runtime_setup.sh
|  |  |  ├── uninstall.sh
|  |  |  ├── src/plugin_name/src/config/settings/settings.py (Optional Django setting file)
```

#### Plugin Boilerplate

With the plugin boilerplate you can easily create a new plugin and setup a docker development environment that installs
adl as a dependency. This can easily be installed via cookiecutter.

##### Creating a plugin

To use the plugin boilerplate you must first install
the [Cookiecutter](https://cookiecutter.readthedocs.io/en/stable/installation.html) tool (`pip install cookiecutter`).

Once you have installed Cookiecutter you can execute the following command to create a new ADL plugin from our
template. In this guide we will name our plugin “My Climweb Plugin”, however you can choose your own plugin name
when prompted to by Cookiecutter.

```{note}
The python module depends on your chosen plugin name. If we for example go with “My Climweb Plugin” the Django app 
name should be my_climweb_plugin
```

```sh
cookiecutter gh:wmo-raf/climweb --directory plugin-boilerplate
project_name [My Climweb Plugin]: 
project_slug [my-climweb-plugin]: 
project_module [my_climweb_plugin]:
```

If you do not see any errors it means that your plugin has been created.

### Writing a Plugin

Now you have created a plugin, lets go into more detail of how to actually extend and customize Climweb using your
plugin.

#### Storing State

If your plugin needs to store state, you should only ever do this in:

- The database being used by Climweb
- Using Django’s default storage mechanism
- The Redis being used by Climweb, but only for non-persistent state like a cache that is fine to be destroyed at any
  moment.

```{note}
Never store any state in your plugin folder itself inside the container. This folder is deleted and recreated as part
of the plugin installation process and any state you store inside it can be lost.
```

#### Adding Python Requirements

Your plugin is just a normal python module which will be installed into the Climweb virtual environment using
`pip` by `install_plugin.sh`. If using the plugin boilerplate you can add any python requirements to the pip
requirements file found at `requirements/base.txt`.

#### As a Django/Wagtail App

When the Climweb Django service starts up it looks for any plugins in the plugin directory. If it finds any it assumes
the `src/plugin_name/` sub folder contains a Django App and adds it to the`INSTALLED_APPS`. This means that your plugin
must be a Django/Wagtail app whose name exactly matches the name of the plugin folder.

In your plugin’s Django/Wagtail app you can do anything that you normally can do with a Django/Wagtail app such as
having migrations, using the `ready()` method to do startup configuration etc.

#### Publishing your Plugin

The easiest way to share you plugin with others is by making a `public` git repository using GitHub,GitLab or some other
git host. Once you have pushed your plugin folder to the git repository then anyone can then install your plugin
following the steps in the Plugin Installation guide.