import { Filter, ChevronDown } from 'lucide-react';

export default function FilterPanel() {
  const filterCategories = [
    {
      name: 'Technology',
      options: ['Artificial Intelligence', 'Machine Learning', 'Computer Vision', 'Agriculture', 'Blockchain', 'IoT'],
    },
    {
      name: 'Filing Year',
      options: ['2024', '2023', '2022', '2021', '2020'],
    },
    {
      name: 'Organization',
      options: ['ABC Technologies', 'AgriTech Innovations', 'GreenFuture Labs', 'HealthChain Systems'],
    },
    {
      name: 'IPC Classification',
      options: ['A01G', 'A01M', 'G06F', 'G16H', 'H01M', 'H04L'],
    }
  ];

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5">
      <div className="flex items-center gap-2 mb-6 pb-4 border-b border-slate-100">
        <Filter className="w-5 h-5 text-indigo-600" />
        <h2 className="text-lg font-semibold text-slate-900">Filters</h2>
      </div>

      <div className="space-y-6">
        {filterCategories.map((category) => (
          <div key={category.name}>
            <button className="flex items-center justify-between w-full text-left mb-3">
              <span className="font-medium text-sm text-slate-900">{category.name}</span>
              <ChevronDown className="w-4 h-4 text-slate-400" />
            </button>
            <div className="space-y-2">
              {category.options.map((option) => (
                <label key={option} className="flex items-center">
                  <input
                    type="checkbox"
                    className="w-4 h-4 text-indigo-600 border-slate-300 rounded focus:ring-indigo-500 cursor-pointer"
                  />
                  <span className="ml-2 text-sm text-slate-600 cursor-pointer hover:text-slate-900 transition-colors">
                    {option}
                  </span>
                </label>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
