Vue.component('errors-table', {
  template: `
<table class="table table-striped text-small">
  <thead>
    <tr>
      <th>Filename</th>
      <th>Owner</th>
      <th>Size</th>
      <th>Reason</th>
      <th></th>
    </tr>
  </thead>
  <tbody>
  <tr v-for="upload in uploads">
    <td>
      <span class="subtitle">&lt;root&gt;/</span><span><strong>{{ getFilePath(upload, root_path) }}</strong></span>
      <div><span class="subtitle">Obs Date:</span> {{ upload.file_date }}</div>
    </td>
    <td>
      <a v-if="upload.organisation" :href='getOrganisationURL(upload)' target="_blank">{{ upload.organisation.subdomain }}</a>
      <a v-else-if="upload.astronomer" :href='getProfileURL(upload)' target="_blank">@{{ upload.astronomer }}</a>
    </td>
    <td>
      {{ getFormattedSize(upload.file_size) }}
    </td>
    <td>
      {{ upload.error }}
    </td>
    <td>
      <button class="btn btn-sm btn-primary-black" @click="sendRetryCommand(upload)">Retry</button>
      <span>&nbsp;</span>
      <button class="btn btn-sm btn-primary-black" @click="sendIgnoreCommand(upload)">Ignore</button>
    </td>
  </tr>
  </tbody>
</table>
`,
  props: {
    root_path: {
      type: String,
      required: true
    },
    uploads: {
      type: Array,
      required: false,
      default () {
        return []
      }
    }
  },
  methods: {
    sendRetryCommand (upload) {
      fetch('/retry?ids=' + upload.id.toString())
    },
    sendIgnoreCommand (upload) {
      fetch('/ignore?ids=' + upload.id.toString())
    }
  }
})
