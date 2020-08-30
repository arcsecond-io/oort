Vue.component('active-table', {
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
    <th>Progress</th>
    <th>Started</th>
    <th>Ended</th>
    <th>Duration</th>
    <th>Error</th>
  </tr>
  </thead>
  <tbody>
  <tr v-for="upload in uploads">
    <td>
      {{ upload.file_path }}
      <div class="subtitle">Obs Date: {{ upload.file_date }}</div>
    </td>
    <td>
      <a v-if="upload.organisation" :href='getOrganisationDatasetURL(upload)' target="_blank">
        {{ upload.dataset.name }}
      </a>
      <a v-else :href='getDatasetURL(upload)' target="_blank">
        {{ upload.dataset.name }}
      </a>
      <div class="subtitle">{{ upload.dataset.uuid }}</div>
    </td>
    <td>
      <a v-if="upload.organisation" :href='getOrganisationNightLogURL(upload)' target="_blank">
        {{ upload.night_log.date }}
      </a>
      <a v-else :href='getNightLogURL(upload)' target="_blank">
        {{ upload.night_log.date }}
      </a>
      <div class="subtitle">{{ upload.night_log.uuid }}</div>
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
      {{ upload.status }}
      <div class="subtitle">{{ upload.substatus }}</div>
    </td>
    <td>
      <div class="progress" style="width: 90%;">
        <div class="progress-bar progress-bar-striped active"
             role="progressbar"
             aria-valuenow="0"
             aria-valuemin="0"
             aria-valuemax="100">
          <span class="progress-bar-label">{{ upload.progress.toFixed(2) }}%</span>
        </div>
      </div>
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
    uploads: {
      type: Array,
      required: false,
      default () {
        return []
      }
    },
    progresses: {
      type: Array,
      required: false,
      default () {
        return []
      }
    }
  },
  watch: {
    progresses (newValues) {
      const bars = document.getElementsByClassName('progress-bar')
      newValues.forEach((progress, index) => {
        let bar = bars[index]
        if (bar) {
          bar.style.width = progress.toFixed(1).toString() + '%'
        }
      })
    }
  },
  methods: {
    getOrganisationDatasetURL (upload) {
      return 'https://' + upload.organisation.subdomain + '.arcsecond.io/data/' + upload.night_log.date
    },
    getDatasetURL (upload) {
      return 'https://www.arcsecond.io/datasets/' + upload.dataset.uuid
    },
    getOrganisationNightLogURL (upload) {
      return 'https://' + upload.organisation.subdomain + '.arcsecond.io/nights/' + upload.night_log.date
    },
    getNightLogURL (upload) {
      return 'https://www.arcsecond.io/nightlogs/' + upload.night_log.uuid
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
    }
  }
})
