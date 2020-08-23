Vue.component('pending-table', {
  template: `
<table class="table table-striped text-small">
  <thead>
  <tr>
    <th>Filename</th>
    <th>Owner</th>
    <th>Size</th>
    <th>Status</th>
  </tr>
  </thead>
  <tbody>
  <tr v-for="upload in uploads">
    <td>
      {{ upload.file_path }}
      <div class="subtitle">Obs Date: {{ upload.file_date }}</div>
    </td>
    <td>
      <a v-if="upload.organisation" :href='getOrganisationURL(upload)' target="_blank">{{ upload.organisation.subdomain }}</a>
      <a v-else :href='getProfileURL(upload)' target="_blank">@{{ upload.astronomer }}</a>
    </td>
    <td>
      {{ getFormattedSize(upload.file_size) }}
    </td>
    <td>
      {{ upload.status }}
      <div class="subtitle">{{ upload.substatus }}</div>
    </td>
  </tr>
  </tbody>
</table>
`,
  props: {
    uploads: {
      type: Array,
      required: false,
      default () {
        return []
      }
    }
  },
  methods: {
    getProfileURL (upload) {
      return 'https://www.arcsecond.io/@' + upload.astronomer
    },
    getOrganisationURL (upload) {
      return 'https://' + upload.organisation.subdomain + '.arcsecond.io'
    },
    getFormattedSize (bytes, decimals) {
      if (bytes === 0) return '0 Bytes'
      const k = 1024
      const dm = decimals || 2
      const sizes = ['Bytes', 'kB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB']
      const i = Math.floor(Math.log(bytes) / Math.log(k))
      return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i]
    }
  }
})
