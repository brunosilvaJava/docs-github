Source: https://docs.github.com/en/enterprise-server@3.15/support/contacting-github-support/providing-data-to-github-support

# Providing data to GitHub Support - GitHub Enterprise Server 3.15 Docs

Since GitHub Support doesn't have access to your environment, we sometimes require some additional information from you.

## Who can use this feature?

Site administrators and enterprise owners can provide data to GitHub Support.

## About diagnostic files and support bundles

To help you troubleshoot issues with a GitHub Enterprise Server instance in your environment, GitHub Support may request one or more types of data.

| Data | File format | Description |
| --- | --- | --- |
| Diagnostic file | Plaintext | Contains information about the instance's settings and environment. |
| Support bundle | Archive | Contains a diagnostics file and sanitized log files from the past two days by default. |
| Extended support bundle | Archive | Contains a diagnostics file and sanitized log files from the past eight days. |

## About log file sanitization

Authentication tokens, keys, and secrets are removed from log files in the following log directories contained within a support bundle or diagnostics file:

- alambic-logs
- babeld-logs
- codeload-logs
- enterprise-manage-logs
- github-logs
- hookshot-logs
- lfs-server-logs
- semiotic-logs
- task-dispatcher-logs
- pages-logs
- registry-logs
- render-logs
- svn-bridge-logs

## Creating and sharing diagnostic files

Diagnostic files are an overview of a GitHub Enterprise Server instance's settings and environment that contain:

- Client license information, including company name, expiration date, and number of user licenses
- Version numbers and SHAs
- VM architecture
- Host name, private mode, SSL settings
- Load and process listings
- Network settings
- Authentication method and details
- Number of repositories, users, and other installation data

You can download the diagnostics for your instance from the Management Console or by running the ghe-diagnostics command-line utility.

### Creating a diagnostic file from the Management Console

You can create a diagnostic file from the Management Console if you don't currently have SSH access.

From an administrative account on GitHub Enterprise Server, in the upper-right corner of any page, click .

If you're not already on the "Site admin" page, in the upper-left corner, click Site admin.

In the " Site admin" sidebar, click Management Console.

If you have created multiple Management Console user accounts, select Root site admin or Management Console user. For more information about Management Console user accounts see, Managing access to the Management Console.

Type your Management Console credentials. Then click Continue.

In the top navigation bar, click Support.

Screenshot of the header of the Management Console. A tab, labeled "Support", is highlighted with an orange outline.

Click Download diagnostics info.

### Creating a diagnostic file using SSH

You can use this method without signing into the Management Console.

Use the ghe-diagnostics command-line utility to retrieve the diagnostics for your instance.

```shell
ssh -p122 admin@HOSTNAME -- 'ghe-diagnostics' > diagnostics.txt
```

## Creating and sharing support bundles

After you submit your support request, we may ask you to share a support bundle with our team. The support bundle is a gzip-compressed tar archive that includes diagnostics and important logs from your instance, such as:

- Authentication-related logs that may be helpful when troubleshooting authentication errors, or configuring LDAP, CAS, or SAML
- Management Console log
- github-logs/exceptions.log: Information about 500 errors encountered on the site
- github-logs/audit.log: GitHub Enterprise Server audit logs
- babeld-logs/babeld.log: Git proxy logs
- system-logs/haproxy.log: HAProxy logs
- elasticsearch-logs/github-enterprise.log: Elasticsearch logs
- configuration-logs/: GitHub Enterprise Server configuration logs
- collectd/logs/collectd.log: Collectd logs
- mail-logs/mail.log: SMTP email delivery logs

For more information, see Audit log for an enterprise.

Support bundles include logs from the past two days by default. You can specify an exact duration in days. To provide logs from the past eight days, you can download an extended support bundle. For more information, see Creating and sharing extended support bundles.

> **Tip**
>
> When you contact GitHub Support, you'll be sent a confirmation email that will contain a ticket reference link. If GitHub Support asks you to upload a support bundle, you can use the ticket reference link to upload the support bundle.

### Creating a support bundle from the Management Console

You can use these steps to create and share a support bundle if you can access the web-based Management Console and have outbound internet access.

From an administrative account on GitHub Enterprise Server, in the upper-right corner of any page, click .

If you're not already on the "Site admin" page, in the upper-left corner, click Site admin.

In the " Site admin" sidebar, click Management Console.

If you have created multiple Management Console user accounts, select Root site admin or Management Console user. For more information about Management Console user accounts see, Managing access to the Management Console.

Type your Management Console credentials. Then click Continue.

In the top navigation bar, click Support.

Screenshot of the header of the Management Console. A tab, labeled "Support", is highlighted with an orange outline.

Click Download support bundle.

If a support engineer has given you an upload link for your support bundle, use this link. Otherwise, visit https://support.github.com/ and sign in (if prompted) to an enterprise account that is entitled to support.

Visit https://support.github.com/uploads and upload your support bundle.

### Creating a support bundle using SSH

You can use these steps to create and share a support bundle if you have SSH access to your GitHub Enterprise Server instance and have outbound internet access.

> **Note**
>
> If your GitHub Enterprise Server instance is in a geo-replication configuration, or if your instance is a cluster, you should use the ghe-cluster-support-bundle command to retrieve the support bundle. For more information, see Command-line utilities.

Download the support bundle via SSH:

```shell
ssh -p 122 admin@HOSTNAME -- 'ghe-support-bundle -o' > support-bundle.tgz
```

For more information about the ghe-support-bundle command, see Command-line utilities.

If a support engineer has given you an upload link for your support bundle, use this link. Otherwise, visit https://support.github.com/ and sign in (if prompted) to an enterprise account that is entitled to support.

Visit https://support.github.com/uploads and upload your support bundle.

### Uploading a support bundle using your enterprise account

Navigate to GitHub Enterprise Cloud.

In the top-right corner of GitHub, click your profile picture.

Depending on your environment, click Enterprise, or click Enterprises then click the enterprise you want to view.

On the left side of the page, in the enterprise account sidebar, click Settings.

Under Settings, click License.

Under "GitHub Enterprise Help", click Upload a support bundle.

Screenshot of the "GitHub Enterprise help" section of the enterprise settings page. The "Upload a support bundle link" is outlined in orange.

Under "Select an enterprise account", use the drop-down menu to select the support bundle's associated account.

Under "Upload a support bundle for GitHub Enterprise Support", to select your support bundle, click Choose file, or drag your support bundle file onto Choose file.

Click Upload.

### Uploading a support bundle directly using SSH

You can directly upload a support bundle to our server if:

- You have SSH access to your GitHub Enterprise Server instance.
- Outbound HTTPS connections over TCP port 443 are allowed from your GitHub Enterprise Server instance to enterprise-bundles.github.com and esbtoolsproduction.blob.core.windows.net.

Upload the bundle to our support bundle server:

```shell
ssh -p122 admin@HOSTNAME -- 'ghe-support-bundle -u'
```

## Creating and sharing extended support bundles

Support bundles include logs from the past two days by default, while extended support bundles include logs from the past eight days. If the events that GitHub Support is investigating occurred more than two days ago, we may ask you to share an extended support bundle. You will need SSH access to download an extended bundle - you cannot download an extended bundle from the Management Console.

To prevent bundles from becoming too large, bundles only contain logs that haven't been rotated and compressed. Log rotation on GitHub Enterprise Server happens at various frequencies (daily or weekly) for different log files, depending on how large we expect the logs to be.

### Creating an extended support bundle using SSH

You can use these steps to create and share an extended support bundle if you have SSH access to your GitHub Enterprise Server instance and you have outbound internet access.

Download the extended support bundle via SSH by adding the -x flag to the ghe-support-bundle command:

```shell
ssh -p 122 admin@HOSTNAME -- 'ghe-support-bundle -o -x' > support-bundle.tgz
```

If a support engineer has given you an upload link for your support bundle, use this link. Otherwise, visit https://support.github.com/ and sign in (if prompted) to an enterprise account that is entitled to support.

Visit https://support.github.com/uploads and upload your support bundle.

### Uploading an extended support bundle directly using SSH

You can directly upload a support bundle to our server if:

- You have SSH access to your GitHub Enterprise Server instance.
- Outbound HTTPS connections over TCP port 443 are allowed from your GitHub Enterprise Server instance to enterprise-bundles.github.com and esbtoolsproduction.blob.core.windows.net.

Upload the bundle to our support bundle server:

```shell
ssh -p122 admin@HOSTNAME -- 'ghe-support-bundle -u -x'
```

## Further reading

- About GitHub Support
- Generating a Health Check for your enterprise
