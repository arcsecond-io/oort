Vue.component('pending-table', {
  template: `
<table class="table table-striped text-small">
  <thead>
  <tr>
    <th>Filename</th>
    <th>Size</th>
    <th>Status</th>
  </tr>
  </thead>
  <tbody>
  <tr v-for="upload in uploads">
    <td>
      <span class="subtitle">&lt;root&gt;/</span><span><strong>{{ getFilePath(upload, root_path) }}</strong></span>
      <div><span class="subtitle">Obs Date:</span> {{ upload.file_date }}</div>
    </td>
    <td>
      {{ getFormattedSize(upload.file_size || upload.file_size_zipped) }}
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
