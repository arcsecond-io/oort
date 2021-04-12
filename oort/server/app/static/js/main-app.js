Vue.component('v-select', VueSelect.VueSelect)

var app = new Vue({
  el: '#vuejs',
  data: {
    source: null,
    has_state: false,
    state: { folders: [] },
    selected_folder: null,
    pending_uploads: [],
    current_uploads: [],
    finished_uploads: [],
    error_uploads: [],
    progresses: [],
    show_tables: {
      pending: true,
      current: true,
      finished_done: true,
      finished_skipped: true,
      error: true
    },
    finished_count: 0,
    skipped_count: 0
  },
  computed: {
    selectButtonTitle () {
      return this.selected_folder ? this.selected_folder.path : '-'
    }
  },
  watch: {
    selected_folder (new_folder) {
      this.reset()
    }
  },
  mounted () {
    const self = this
    this.source = new EventSource('/uploads')
    this.source.onmessage = function (event) {
      const json_data = JSON.parse(event.data)

      self.state = json_data.state
      self.has_state = true
      if (!self.selected_folder && self.state.folders.length > 0) {
        self.selected_folder = self.state.folders[0]
      }

      self.pending_uploads = json_data.pending.filter(u => u.file_path.startsWith(self.selectButtonTitle))
      self.current_uploads = json_data.current.filter(u => u.file_path.startsWith(self.selectButtonTitle))
      self.error_uploads = json_data.errors.filter(u => u.file_path.startsWith(self.selectButtonTitle))

      self.finished_uploads = json_data.finished
        .filter(u => u.file_path.startsWith(self.selectButtonTitle))
        .filter(u => (u.substatus.toLowerCase().startsWith('skipped') && self.show_tables.finished_skipped) || (!u.substatus.toLowerCase().startsWith('skipped') && self.show_tables.finished_done))

      self.finished_count = self.finished_uploads.length
      self.skipped_count = self.finished_uploads.filter(u => u.substatus.toLowerCase().startsWith('skipped')).length
      self.progresses = self.current_uploads.map(u => u.progress)
    }
  },
  methods: {
    reset () {
      this.pending_uploads = []
      this.current_uploads = []
      this.finished_uploads = []
      this.error_uploads = []
      this.progresses = []
      this.finished_count = 0
      this.skipped_count = 0
    },
    retryAllFailed () {
      fetch('/retry?ids=' + this.error_uploads.reduce((acc, value) => acc + value.id.toString() + ',', ''))
    }
  }
})


