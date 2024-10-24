# Live contexts

This page describes the contexts a [live workflow](live-workflow-syntax.md#live-workflow) can use in expressions for calculating YAML attribute values.

## Live Contexts

| Context name | Description |
| :--- | :--- |
| `env` | Contains environment variables set in a workflow or a job. For more information, see [`env` context](live-contexts.md#env-context) . |
| `flow` | Information about the main workflow settings, defaults, etc. See [`flow` context](live-contexts.md#flow-context) for details. |
| `project` | Information about the project. See [`project` context](live-contexts.md#project-context) for details. |
| `images` | Contains a mapping of images on the Neu.ro registry. See [`images` context](live-contexts.md#images-context) for details. |
| `multi` | Multi-job context. For more information, see [`multi` context](live-contexts.md#multi-context). |
| `params` | A mapping of global workflow parameters. For more information, see [`params` context](live-contexts.md#params-context). |
| `tags` | A set of job tags set in a workflow or a job. See [`tags` context](live-contexts.md#tags-context) for details. |
| `volumes` | Contains a mapping of volume definitions. For more information, see [`volumes` context](live-contexts.md#volumes-context). |
| `git` | A mapping of the project's workspace to a git repository. For more information, see [`git` context](live-contexts.md#git-context). |

### `env` context

The `env` context contains environment variables that have been set in a workflow or a job. For more information about setting environment variables in your workflow, see "[Live workflow syntax](live-workflow-syntax.md#live-workflow)."

The `env` context syntax allows you to use the value of an environment variable in your workflow file. If you want to use the value of an environment variable inside a job, use your operating system's standard method for reading environment variables.

| Property name | Type | Description |
| :--- | :--- | :--- |
| `env.<env-name>` | `str` | The value of a specific environment variable. |

### `flow` context

The `flow` context contains information about the workflow: its id, title, etc.

| Property name | Type | Description |
| :--- | :--- | :--- |
| `flow.flow_id` | `str` | The workflow's ID. It's automatically generated based on the workflow's YAML filename with a dropped suffix \(this will always `'live'` in live mode\). You can override the property by setting the [`flow.id`](live-workflow-syntax.md#id) attribute. |
| `flow.project_id` | `str` | The project's ID. It is automatically generated based on the name of the project folder. You can override it using [`project.id`](project-configuration-syntax.md#id) attribute. Check [the project configuration](project-configuration-syntax.md) for details. |
| `flow.workspace` | `LocalPath` | A path to the workspace \(the root folder of the project\). |
| `flow.title` | `str` | The workflow title. Set the [`flow.title`](live-workflow-syntax.md#title) attribute to override the auto-generated value. |

### `project` context

The `project`context contains information about the project: its ID, owner, etc.

| Property name | Type | Description |
| :--- | :--- | :--- |
| `project.id` | `str` | The project's ID. It is automatically generated based on the name of the project folder. You can override it using [`project.id`](project-configuration-syntax.md#id) attribute. Check [the project configuration](project-configuration-syntax.md) for details. This context property is an alias to `flow.project_id` . |
| `project.owner` | `str` | The project's owner. See also: [the project configuration](project-configuration-syntax.md#owner). |
| `project.role` | `str` | The project's role. Set the [`project.role`](project-configuration-syntax.md#role) attribute to override the auto-calculated value. |

### `images` context

Contains information about images defined in the [`images` section](live-workflow-syntax.md#images) of a _live_ workflow.

<table>
  <thead>
    <tr>
      <th style="text-align:left">Property name</th>
      <th style="text-align:left">Type</th>
      <th style="text-align:left">Description</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td style="text-align:left"><code>images.&lt;image-id&gt;.id</code>
      </td>
      <td style="text-align:left"><code>str</code>
      </td>
      <td style="text-align:left">The image definition identifier. For more information, see <a href="live-workflow-syntax.md#images-less-than-image-id-greater-than"><code>images.&lt;image-id&gt;</code></a> section.</td>
    </tr>
    <tr>
      <td style="text-align:left"><code>images.&lt;image-id&gt;.ref</code>
      </td>
      <td style="text-align:left"><code>str</code>
      </td>
      <td style="text-align:left">The image reference. For more information, see <a href="live-workflow-syntax.md#images-less-than-image-id-greater-than-ref"><code>images.&lt;image-id&gt;.ref</code></a> attribute.</td>
    </tr>
    <tr>
      <td style="text-align:left"><code>images.&lt;image-id&gt;.context</code>
      </td>
      <td style="text-align:left"><code>LocalPath</code> or <code>None</code>
      </td>
      <td style="text-align:left">
        <p>The context directory used for building the image or <code>None</code> if
          the context is not set. The path is relative to the project&apos;s root
          (<code>flow.workspace</code> property).</p>
        <p>For more information, see <a href="live-workflow-syntax.md#images-less-than-image-id-greater-than-context"><code>images.&lt;image-id&gt;.context</code> attribute</a>.</p>
      </td>
    </tr>
    <tr>
      <td style="text-align:left"><code>images.&lt;image-id&gt;.full_context_path</code>
      </td>
      <td style="text-align:left"><code>LocalPath</code> or <code>None</code>
      </td>
      <td style="text-align:left">The absolute path, pointing to the <code>context</code> folder if set.</td>
    </tr>
    <tr>
      <td style="text-align:left"><code>images.&lt;image-id&gt;.dockerfile</code>
      </td>
      <td style="text-align:left"><code>LocalPath</code>or <code>None</code>
      </td>
      <td style="text-align:left">
        <p>A path to <code>Dockerfile</code> or <code>None</code> if not set.</p>
        <p>For more information, see <a href="live-workflow-syntax.md#images-less-than-image-id-greater-than-dockerfile"><code>images.&lt;image-id&gt;.dockerfile</code> attribute</a>.</p>
      </td>
    </tr>
    <tr>
      <td style="text-align:left"><code>images.&lt;image-id&gt;.full_dockerfile_path</code>
      </td>
      <td style="text-align:left"><code>LocalPath</code> or <code>None</code>
      </td>
      <td style="text-align:left">Full version of the <code>dockerfile</code> attribute.</td>
    </tr>
    <tr>
      <td style="text-align:left"><code>images.&lt;image-id&gt;.build_args</code>
      </td>
      <td style="text-align:left"><code>list[str]</code>
      </td>
      <td style="text-align:left">
        <p>A sequence of additional build arguments.</p>
        <p>For more information, see <a href="live-workflow-syntax.md#images-less-than-image-id-greater-than-build_args"><code>images.&lt;image-id&gt;.build_args</code> attribute</a>.</p>
      </td>
    </tr>
    <tr>
      <td style="text-align:left"><code>images.&lt;image-id&gt;.env</code>
      </td>
      <td style="text-align:left"><code>dict[str, str]</code>
      </td>
      <td style="text-align:left">
        <p>Environment variables passed to the image builder.</p>
        <p>For more information, see <a href="live-workflow-syntax.md#images-less-than-image-id-greater-than-env"><code>images.&lt;image-id&gt;.env</code> attribute</a>.</p>
      </td>
    </tr>
    <tr>
      <td style="text-align:left"><code>images.&lt;image-id&gt;.volumes</code>
      </td>
      <td style="text-align:left"><code>list[str]</code>
      </td>
      <td style="text-align:left">
        <p>A sequence of volume definitions passed to the image builder.</p>
        <p>For more information, see <a href="live-workflow-syntax.md#images-less-than-image-id-greater-than-volumes"><code>images.&lt;image-id&gt;.volumes</code> attribute.</a>
        </p>
      </td>
    </tr>
  </tbody>
</table>

### `multi` context

The additional arguments passed to _multi-job_.

<table>
  <thead>
    <tr>
      <th style="text-align:left">Property name</th>
      <th style="text-align:left">Type</th>
      <th style="text-align:left">Description</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td style="text-align:left"><code>multi.args</code>
      </td>
      <td style="text-align:left"><code>str</code>
      </td>
      <td style="text-align:left">
        <p>Additional command line arguments passed to <em>multi-job</em>.
          <br />The command line run defines the field as <code>neuro-flow run &lt;job-id&gt; -- &lt;args&gt;</code>.</p>
        <p><code>multi.args</code> is mainly used for passing args to command line
          parameters accepted by <em>multi-job</em>, see <a href="live-workflow-syntax.md#jobs-less-than-job-id-greater-than-cmd"><code>jobs.&lt;job-id&gt;.cmd</code></a> for
          details.</p>
      </td>
    </tr>
    <tr>
      <td style="text-align:left"><code>multi.suffix</code>
      </td>
      <td style="text-align:left"><code>str</code>
      </td>
      <td style="text-align:left"><em>multi-job</em> suffix added to <a href="live-workflow-syntax.md#jobs-job-id-env"><code>jobs.&lt;job-id&gt;</code></a>.</td>
    </tr>
  </tbody>
</table>

### `params` context

Parameter described in the [`jobs.<job-id>.params` attribute](live-workflow-syntax.md#jobs-less-than-job-id-greater-than-params) and available for substitution - for example, in [`jobs.<job-id>.cmd`](live-workflow-syntax.md#jobs-less-than-job-id-greater-than-cmd) calculation.

| Property name | Type | Description |
| :--- | :--- | :--- |
| `params.<param-name>` | `str` | The value of a specific parameter. |

Supported parameter values: `project`, `flow`, `env`, `tags`, `volumes`, `images`.

### `tags` context

A set of job tags.

Tags are combined from system tags \(`project:<project-id>`, `job:<job-id>`\), flow default tags \(see [`defaults.tags` attribute](live-workflow-syntax.md#defaults-tags)\), and job-specific tags \(see `jobs.<job-id>.tags` attribute\).

| Property name | Type | Description |
| :--- | :--- | :--- |
| `tags` | `set[str]` | This context changes for each job. You can access this context from any job. |

### `volumes` context

Contains information about volumes defined in the [`volumes` section ](live-workflow-syntax.md#volumes) of a _live_ workflow.

<table>
  <thead>
    <tr>
      <th style="text-align:left">Property name</th>
      <th style="text-align:left">Type</th>
      <th style="text-align:left">Description</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td style="text-align:left"><code>volumes.&lt;volume-id&gt;.id</code>
      </td>
      <td style="text-align:left"><code>str</code>
      </td>
      <td style="text-align:left">The volume definition identifier. For more information, see <a href="live-workflow-syntax.md#volumes-less-than-volume-id-greater-than"><code>volumes.&lt;volume-id&gt;</code> section</a>.</td>
    </tr>
    <tr>
      <td style="text-align:left"><code>volumes.&lt;volume-id&gt;.remote</code>
      </td>
      <td style="text-align:left"><code>URL</code>
      </td>
      <td style="text-align:left">Remote volume URI, e.g. <code>storage:path/to</code>.
        <br />For more information, see <a href="live-workflow-syntax.md#volumes-less-than-volume-id-greater-than-remote"><code>volumes.&lt;volume-id&gt;.remote</code> attribute</a>.</td>
    </tr>
    <tr>
      <td style="text-align:left"><code>volumes.&lt;volume-id&gt;.mount</code>
      </td>
      <td style="text-align:left"><code>RemotePath</code>
      </td>
      <td style="text-align:left">
        <p>The path inside a job by which the volume should be mounted.</p>
        <p>For more information, see <a href="live-workflow-syntax.md#volumes-less-than-volume-id-greater-than-mount"><code>volumes.&lt;volume-id&gt;.mount</code> attribute</a>.</p>
      </td>
    </tr>
    <tr>
      <td style="text-align:left"><code>volumes.&lt;volume-id&gt;.read_only</code>
      </td>
      <td style="text-align:left"><code>bool</code>
      </td>
      <td style="text-align:left">
        <p><code>True</code> if the volume is mounted in read-only mode, <code>False</code> otherwise.</p>
        <p>For more information, see <a href="live-workflow-syntax.md#volumes-less-than-volume-id-greater-than-read_only"><code>volumes.&lt;volume-id&gt;.read_only</code> attribute</a>.</p>
      </td>
    </tr>
    <tr>
      <td style="text-align:left"><code>volumes.&lt;volume-id&gt;.local</code>
      </td>
      <td style="text-align:left"><code>LocalPath</code>or <code>None</code>
      </td>
      <td style="text-align:left">
        <p>A path in the workspace folder to synchronize with remote Neu.ro storage
          or <code>None</code> if not set.</p>
        <p>For more information, see <a href="live-workflow-syntax.md#volumes-less-than-volume-id-greater-than-local"><code>volumes.&lt;volume-id&gt;.local</code> attribute</a>.</p>
      </td>
    </tr>
    <tr>
      <td style="text-align:left"><code>volumes.&lt;volume-id&gt;.full_local_path</code>
      </td>
      <td style="text-align:left"><code>LocalPath</code> or <code>None</code>
      </td>
      <td style="text-align:left">Full version of <code>local</code> property.</td>
    </tr>
    <tr>
      <td style="text-align:left"><code>volumes.&lt;volume-id&gt;.ref</code>
      </td>
      <td style="text-align:left"><code>str</code>
      </td>
      <td style="text-align:left">
        <p>A volume reference that can be used as a <a href="live-workflow-syntax.md#jobs-less-than-job-id-greater-than-volumes"><code>jobs.&lt;job-id&gt;.volumes</code> item</a>.
          The calculated value looks like <code>storage:path/to:/mnt/path:rw</code>.</p>
        <p>The value is assembled from <code>remote</code>, <code>mount</code>, and <code>read_only</code> properties.</p>
      </td>
    </tr>
    <tr>
      <td style="text-align:left"><code>volumes.&lt;volume-id&gt;.ref_ro</code>
      </td>
      <td style="text-align:left"><code>str</code>
      </td>
      <td style="text-align:left">Like <code>ref</code> but <em>read-only</em> mode is enforced.</td>
    </tr>
    <tr>
      <td style="text-align:left"><code>volumes.&lt;volume-id&gt;.ref_rw</code>
      </td>
      <td style="text-align:left"><code>str</code>
      </td>
      <td style="text-align:left">Like <code>ref</code> but <em>read-write</em> mode is enforced.</td>
    </tr>
  </tbody>
</table>

### `git` context

The `git` context contains contains a mapping of your project's workspace to a git repository.

This context can only be used if the project's workspace is inside some git repository.

| Property name | Type | Description |
| :--- | :--- | :--- |
| `git.sha` | `str` | SHA of the current commit. |
| `git.branch` | `str` | Name of the current branch. |
| `git.tags` | `list[str]` | List of tags that point to the current commit. |
