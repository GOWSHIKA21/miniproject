export default function FeatureCard({ icon: Icon, title, description, isDarkTheme }) {
  return (
    <div className={`rounded-2xl p-5 border transition-all duration-300 group shadow-sm hover:shadow-md ${
      isDarkTheme 
        ? 'bg-[#1a1236] border-[#2c1f54] hover:border-[#6b46c1]' 
        : 'bg-white border-[#e9e1fa] hover:border-[#6b46c1]'
    }`}>
      <div className="w-10 h-10 rounded-xl bg-[#f3eefc] border border-[#e2d5f8] flex items-center justify-center text-[#6b46c1] mb-3 group-hover:bg-[#6b46c1] group-hover:text-white transition-colors duration-300">
        <Icon className="w-5 h-5" />
      </div>
      <h3 className={`text-base font-bold mb-1.5 ${isDarkTheme ? 'text-white' : 'text-[#2d1f56]'}`}>
        {title}
      </h3>
      <p className={`text-xs leading-relaxed ${isDarkTheme ? 'text-slate-400' : 'text-[#5a478c]'}`}>
        {description}
      </p>
    </div>
  );
}
