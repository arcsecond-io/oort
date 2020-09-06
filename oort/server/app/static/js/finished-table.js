Vue.component('finished-table', {
  template: `
<table class="table table-striped text-small">
  <thead>
  <tr>
    <th>Filename</th>
    <th>Dataset</th>
    <th>Night Log</th>
    <th>Telescope</th>
    <th>Owner</th>
    <th>Size</th>
    <th>Status</th>
    <th>Started</th>
    <th>Ended</th>
    <th>Duration</th>
    <th>Error</th>
  </tr>
  </thead>
  <tbody>
  <tr v-for="upload in uploads">
    <td>
      <span class="subtitle">&lt;root&gt;</span><span><strong>{{ getFilePath(upload) }}</strong></span>
      <div><span class="subtitle">Obs Date:</span> {{ upload.file_date }}</div>
    </td>
    <td>
      <div v-if="upload.dataset">
        <a v-if="upload.organisation" :href='getOrganisationDatasetURL(upload)' target="_blank">
          {{ upload.dataset.name }}
        </a>
        <a v-else :href='getDatasetURL(upload)' target="_blank">
          {{ upload.dataset.name }}
        </a>
        <div class="subtitle">{{ upload.dataset.uuid }}</div>
      </div>
    </td>
    <td>
      <div v-if="upload.night_log && upload.night_log.date">
        <a v-if="upload.organisation" :href='getOrganisationNightLogURL(upload)' target="_blank">
          {{ upload.night_log.date }}
        </a>
        <a v-else :href='getNightLogURL(upload)' target="_blank">
          {{ upload.night_log.date }}
        </a>
        <div class="subtitle">{{ upload.night_log.uuid }}</div>
      </div>
    </td>
    <td>
      <div v-if="upload.telescope">
        {{ upload.telescope.name }}
        <div class="subtitle">{{ upload.telescope.uuid }}</div>
      </div>
      <div v-else>
        <span class="subtitle">(no telescope)</span>
      </div>
    </td>
    <td>
      <a v-if="upload.organisation" :href='getOrganisationURL(upload)' target="_blank">{{ upload.organisation.subdomain }}</a>
      <a v-else :href='getProfileURL(upload)' target="_blank">@{{ upload.astronomer }}</a>
    </td>
    <td>
      {{ getFormattedSize(upload.file_size) }}
    </td>
    <td>
      <div :style="getStatusStyle(upload)">
        {{ upload.status }}
      </div>
      <div class="subtitle">{{ upload.substatus }}</div>
    </td>
    <td>{{ upload.started }}</td>
    <td>{{ upload.ended }}</td>
    <td>{{ upload.duration.toFixed(1) }} s</td>
    <td>{{ upload.error }}</td>
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
    getFilePath(upload) {
      return upload.file_path.replace(this.root_path, '')
    },
    getOrganisationDatasetURL (upload) {
      return 'https://' + upload.organisation.subdomain + '.arcsecond.io/data/' + upload.night_log.date
    },
    getDatasetURL (upload) {
      return (upload.dataset) ? 'https://www.arcsecond.io/datasets/' + upload.dataset.uuid : ''
    },
    getOrganisationNightLogURL (upload) {
      return 'https://' + upload.organisation.subdomain + '.arcsecond.io/nights/' + upload.night_log.date
    },
    getNightLogURL (upload) {
      return (upload.night_log) ? 'https://www.arcsecond.io/nightlogs/' + upload.night_log.uuid : ''
    },
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
    },
    getStatusStyle (upload) {
      return { color: upload.substatus.toLowerCase().startsWith('skipped') ? 'orange' : 'green' }
    }
  }
})
