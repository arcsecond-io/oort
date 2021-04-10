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
      <span class="subtitle">&lt;root&gt;/</span><span><strong>{{ getFilePath(upload, root_path) }}</strong></span>
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
      <div v-else>
        <span class="subtitle">(no night log)</span>
      </div>
    </td>
    <td>
      <div v-if="upload.telescope">
        {{ upload.telescope.name }}
        <div class="subtitle">{{ upload.telescope.uuid }}</div>
      </div>
      <div v-else-if="!upload.telescope && !upload.substatus.toLowerCase().startsWith('skipped')">
        <span class="subtitle">(no telescope)</span>
      </div>
    </td>
    <td>
      <a v-if="upload.organisation" :href='getOrganisationURL(upload)' target="_blank">{{ upload.organisation.subdomain }}</a>
      <a v-else-if="upload.astronomer" :href='getProfileURL(upload)' target="_blank">@{{ upload.astronomer }}</a>
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
    <td>
      <div>
        {{ upload.started }}
      </div>
      <div class="subtitle">
        {{ getTimeAgoString(upload.started) }}
       </div>
    </td>
    <td>
      <div>
        {{ upload.ended }}
      </div>
      <div class="subtitle">
        {{ getTimeAgoString(upload.ended) }}
       </div>
    </td>
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
  }
})
